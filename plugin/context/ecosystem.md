# Peskas ecosystem

Peskas is WorldFish's open-source monitoring platform for small-scale fisheries: country pipelines turn landing surveys and boat GPS tracks into validated catch, effort and revenue data, which feeds public portals, a validation app, an API and a fisher-facing tracks app. Every repo you work in is one node in this graph; a change that looks local often breaks a consumer in another repo.

All repos live under `github.com/WorldFishCenter/` and sit side by side locally (`../<repo>`) when cloned; not everyone clones every repo.

## Repo map

Active:

| Repo | Role | Stack |
|---|---|---|
| `peskas.coasts` (pkg `coasts`) | **Shared hub**: storage/Mongo/KoBo/Airtable helpers, PDS ingestion, WIO regional portal data, tracks-app data | R package |
| `peskas.kenya.data.pipeline` | Kenya: WCS catch + price surveys, KEFS surveys | R package |
| `peskas.zanzibar.data.pipeline` | Zanzibar: WCS, WF, BA, gleaning surveys | R package |
| `peskas.mozambique.data.pipeline` | Mozambique: DINAPA and Lurio form chains (DINAPA's chain is still named `adnap` in code) | R package |
| `peskas.timor.data.pipeline` | Timor-Leste: KoBo landings + PDS, public data, Dataverse | R package |
| `peskas-api` | Serves validated/raw trips parquet from GCS | Python FastAPI + DuckDB, Cloud Run |
| `peskas-validation` | Management/validation portal (repo remote: `peskas.zanzibar.validation`) | React/Vite + Express, Vercel |
| `peskas.dashboard` | Multi-country portal, one Vercel project per `NEXT_PUBLIC_COUNTRY_CODE` (TZ/KE/MZ). Its `shadcn-migration` branch is a rewrite (React/Vite + tRPC on Nitro, `VITE_COUNTRY_CODE`), not yet on `dev` | Next.js 15, Turborepo, Vercel |
| `peskas.timor.portal.v2` | Timor portal | React/Vite, Vercel |
| `coasts` | WIO regional portal (coasts.peskas.org). Not the R package `peskas.coasts`, which produces its data | React/Vite, Vercel, no backend |
| `tracks-explorer` | Fisher-facing tracks app | React/Vite + Capacitor, Vercel |
| `peskas.kenya.bmu.dashboard` | Kenya WCS BMU dashboard with role-based access (WCS + WorldFish) | Next.js + tRPC |

Public names (READMEs, docs, UI copy): Peskas Zanzibar / Kenya / Mozambique (country dashboards), Peskas Timor-Leste, Peskas Coasts, Peskas Tracks, Peskas Kenya BMU dashboard, Peskas Management Platform, Peskas Fishery Data API; pipelines are "Peskas <Country> data pipeline". Spell Peskas, WorldFish, Timor-Leste, KoboToolbox. Public contact: peskas.platform@gmail.com.

Legacy: treat as read-only reference unless the task names them. `peskas.malawi.data.pipeline` (pre-coasts, has its own storage code), `peskas.timor.portal` (Shiny, replaced by v2), `peskas.kenya.v2` (actually the old Zanzibar app), `peskas.mozambique.v2`, `zanzibar-portal`, `mozambique-portal`, `fisher-tracks-app`.

## Data flow

```
KoBo surveys ─┐
PDS GPS API ──┼─► country pipeline ─┬─► own GCS bucket (<country>[-dev])
Airtable ─────┤   (uses coasts::)   ├─► peskas-api-* bucket ─► peskas-api ─► peskas-validation
Sheets ───────┘                     ├─► Mongo validation-* ◄──► peskas-validation ─► KoBo validation status ─► pipelines
                                    ├─► coasts::export_portal ─► Mongo portal-* ─► peskas.dashboard
                                    └─► Mongo <country>-* (own apps / legacy portals)
peskas.coasts ─► Mongo portal-* tracks-app collections ─► tracks-explorer
peskas.coasts ─► Mongo portal + GCS peskas-coasts ─► daily JSON commit to public/data/ ─► coasts portal
Timor only ─► GCS public-timor ─► peskas.timor.portal.v2
Kenya only ─► Mongo app[-dev] ─► peskas.kenya.bmu.dashboard
```

Timor on the coasts portal (`export_portal`) is separate from `peskas.timor.portal.v2` (`public-timor`); changing one does not update the other.

## Cross-repo contracts

Each is a producer/consumer pair across repos. Changing one side means changing the other in the same piece of work, or keeping the old shape alive.

- **Versioned filenames**: `prefix__YYYYMMDDHHMMSS_<sha7>__.ext`, written by `add_version()`, read back as `version = "latest"`. `peskas-api` parses it with the regex `trips-\w+__(\d{14})_[a-f0-9]+__.parquet` on path `{country}/{raw|validated}/`.
- **Validation flags**: pipelines write `surveys_flags-{asset_id}` and `enumerators_stats-{asset_id}` to Mongo `validation-*`; `peskas-validation` reads them and writes a reviewer's decision (`validation_status`, `validated_by`, `validated_at`) into `surveys_flags-*` and to KoBo. Before rewriting, pipelines re-read both (`coasts::review_decisions()`), so renaming one of those three fields silently drops reviewers' decisions. Flag numbers are permanent: append new ones, never renumber or reuse.
- **Portal collections**: `peskas.dashboard` (`dev`) reads `monthly_summaries`, `taxa_summaries`, `districts_summaries`, `gear_summaries` and `grid_summaries` through its default connection (`MONGODB_URI`, `packages/nosql/src/index.ts`), and `wio_gaul2` through `MONGODB_URI_COASTS` (`getPortalDb`, `packages/nosql/src/portal-db.ts`). The `shadcn-migration` rewrite also reads `taxa_traits`, `length_summaries` and `gear_taxa_summaries`, and `pds_effort` and `pds_fishing_grounds` (written by `export_pds_spatial()` in the coasts pipeline, filtered by `country`), which coasts already writes. Renaming a column or collection is a dashboard change too.
- **FishBase traits**: `enrich_taxa()` in the coasts pipeline writes `taxa-fishbase-enriched__*` to the hub bucket; `summarize_data()` in every country pipeline reads it (`metadata.fishbase.taxa_enriched.file_prefix`, defaulting to that name) to build `taxa_traits`. Renaming a column there empties the vulnerable-species and size views of the rewritten dashboard (`shadcn-migration`).
- **API landings schema**: column names and order in the `trips-*` parquet are agreed across all four country pipelines (`export_api_raw/validated`), declared in `peskas-api` (`src/peskas_api/schema/field_metadata.py`), and hard-coded by `peskas-validation` data-explorer lessons (`data-explorer/*.qmd`); its downloads (`lib/peskas-api.js`) hard-code the filter/scope parameters. A column change touches all three.
- **Kenya app DB**: Mongo `app[-dev]` collections written by `peskas.kenya.data.pipeline` are read by `peskas.kenya.bmu.dashboard` schemas in `packages/nosql`.
- **Coasts portal data**: two daily workflows in `coasts` fetch from Mongo `portal` (the `peskas.coasts` production `coasts_portal` database, not `portal-prod`) the collections `wio_gaul1/2`, `metrics_gaul1/2` written by `export_geos()`, and from the `peskas-coasts` bucket the latest `pds-fishing-grounds__*`, `pds-h3-effort-r9__*` (`export_pds_spatial()`) and `frame-gears__*` (`export_frame_data()`) files, then commit JSON to `public/data/`, which redeploys the site. Renaming a collection, column or file prefix in `peskas.coasts` breaks the portal at its next fetch. Money values arrive in USD, converted in `export_geos()`.
- **Timor public bucket**: `portal-*.json` in `public-timor` is fetched by `peskas.timor.portal.v2/scripts/fetchData.js`.
- **coasts version floor**: country pipelines install `coasts` from GitHub (`Remotes:` in DESCRIPTION, `COASTS_REF` build arg in CI). A breaking change in coasts ships as a coasts release first, then each pipeline bumps to it.

## Domain terms

- **PDS**: Pelagic Data Systems, solar GPS trackers on boats; the source of tracks and trips.
- **KoBo**: KoboToolbox, the survey platform enumerators use to record landings.
- **WCS / WF / BA / DINAPA / Lurio / KEFS**: survey programmes or partners, each with its own KoBo form chain.
- **DINAPA**: National Directorate of Fisheries and Aquaculture, Mozambique's fisheries authority; it replaced ADNAP. It has no website or logo yet. Code identifiers (`*_adnap()` functions, `adnap` config keys, `wf-adnap-*` GCS prefixes, `KOBO_ASSET_ID_ADNAP`) keep the old name; published values and user-facing text say DINAPA.
- **Landing / trip**: one boat's fishing trip as recorded at the landing site; the core row across pipelines.
- **Enumerator**: the person recording landings; validation scores them in `enumerators_stats`.
- **GAUL**: FAO administrative boundaries used for regional aggregation (`wio_gaul1/2`).
