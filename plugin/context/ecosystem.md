# Peskas ecosystem

Peskas is WorldFish's open-source monitoring platform for small-scale fisheries: country pipelines turn landing surveys and boat GPS tracks into validated catch, effort and revenue data for public portals, a validation app, an API and a fisher-facing tracks app. A change that looks local often breaks a consumer in another repo.

All repos are under `github.com/WorldFishCenter/`, cloned side by side (`../<repo>`); not everyone clones every repo.

## Repo map

Active:

| Repo | Role | Stack |
|---|---|---|
| `peskas.coasts` (pkg `coasts`) | **Shared hub**: storage/Mongo/KoBo/Airtable helpers, PDS ingestion, WIO regional portal data, tracks-app data | R package |
| `peskas.kenya.data.pipeline` | Kenya: WCS catch + price surveys, KEFS surveys | R package |
| `peskas.zanzibar.data.pipeline` | Zanzibar: WCS, WF, BA, gleaning surveys | R package |
| `peskas.mozambique.data.pipeline` | Mozambique: DINAPA and Lurio form chains | R package |
| `peskas.timor.data.pipeline` | Timor-Leste: KoBo landings + PDS, public data, Dataverse | R package |
| `peskas-api` | Serves the countries' landings (validated/raw trips) and district-months parquet from GCS | Python FastAPI + DuckDB, Cloud Run |
| `peskas-validation` | Management/validation portal (repo remote: `peskas.zanzibar.validation`) | React/Vite + Express, Vercel |
| `peskas.dashboard` | Multi-country portal, one Vercel project per `VITE_COUNTRY_CODE` (TZ/KE/MZ) | React/Vite + tRPC on Nitro, Turborepo, Vercel |
| `peskas.timor.portal.v2` | Timor portal | React/Vite, Vercel |
| `coasts` | WIO regional portal (coasts.peskas.org). Not the R package `peskas.coasts`, which produces its data | React/Vite, Vercel, no backend |
| `tracks-explorer` | Fisher-facing tracks app | React/Vite + Capacitor, Vercel |
| `peskas.kenya.bmu.dashboard` | Kenya WCS BMU dashboard, role-based access | Next.js + tRPC |
| `peskas.show` | Public website (peskas.org): blog, links to every portal (`content/global/regions.json`); reads no Peskas data | Next.js, Vercel |

Public names (READMEs, docs, UI copy): Peskas Zanzibar / Kenya / Mozambique (country dashboards), Peskas Timor-Leste, Peskas Coasts, Peskas Tracks, Peskas Kenya BMU dashboard, Peskas Management Platform, Peskas Fishery Data API; pipelines are "Peskas <Country> data pipeline". Spell Peskas, WorldFish, Timor-Leste, KoboToolbox. Public contact: peskas.platform@gmail.com.

Brand: the logo is made in peskas-context `brand/` and `brand/sync.py` copies it to every repo; edit it there.

Legacy (read-only unless the task names them): `peskas.malawi.data.pipeline` (pre-coasts), `peskas.timor.portal` (Shiny, replaced by v2), `peskas.kenya.v2` (the old Zanzibar app), `peskas.mozambique.v2`, `zanzibar-portal`, `mozambique-portal`, `fisher-tracks-app`.

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
Timor only ─► peskas-api-* bucket + peskas-api /metadata ─► Harvard Dataverse (monthly, one versioned dataset)
coasts::export_portal ─► peskas-api-* bucket <country>/aggregated/ ─► peskas-api /data/district-months ─► peskas-validation
Kenya only ─► Mongo app[-dev] ─► peskas.kenya.bmu.dashboard
peskas.coasts ─► Airtable frame collection_stats (weekly)
```

Timor on the coasts portal (`export_portal`) is separate from `peskas.timor.portal.v2` (`public-timor`); changing one does not update the other.

## Cross-repo contracts

Change both sides of a contract in the same piece of work, or keep the old shape alive.

- **Versioned filenames**: `prefix__YYYYMMDDHHMMSS_<sha7>__.ext`, written by `add_version()`, read back as `version = "latest"`. `peskas-api` parses it with the regex `trips-\w+__(\d{14})_[a-f0-9]+__.parquet` on path `{country}/{raw|validated}/`, and `district-months__(\d{14})_[a-f0-9]+__.parquet` on `{country}/aggregated/` (each dataset's pair in `schema/dataset_config.py`).
- **Validation flags**: pipelines write `surveys_flags-{asset_id}` to Mongo `validation-*`, one document per submission with `alert_flag` (the codes) and `alert_catches` (the catch behind each). `peskas-validation` reads it, enumerator stats too since 2.10.0 (`enumerators_stats-*` is still written, unread), and writes a reviewer's decision (`validation_status`, `validated_by`, `validated_at`) into `surveys_flags-*` and to KoBo. Before rewriting, pipelines re-read both (`coasts::review_decisions()`), so renaming one of those three fields silently drops reviewers' decisions. Flag numbers are permanent: append new ones, never renumber or reuse.
- **What "validated" means**: in every country, the validated table (and so the API's `validated` scope) keeps a submission only if it has no flag or a reviewer approved it, and never once a reviewer rejected it.
- **Portal collections**: `peskas.dashboard` reads `monthly_summaries`, `districts_summaries`, `taxa_summaries`, `gear_summaries`, `gear_taxa_summaries`, `length_summaries` and `taxa_traits` through `MONGODB_URI`, and `wio_gaul2`, `pds_effort` and `pds_fishing_grounds` (from `export_pds_spatial()`, filtered by `country`) through `MONGODB_URI_COASTS` (`getPortalDb`), both in `packages/nosql/src/index.ts`. The FAO ARTFISH columns (`*_fao`) need coasts >= 4.19.0 and dashboard >= 2.3.0, and per species in `taxa_summaries` coasts >= 4.23.0 and dashboard >= 2.4.0. coasts still writes `grid_summaries`, which no dashboard reads.
- **FishBase traits**: `enrich_taxa()` in the coasts pipeline writes `taxa-fishbase-enriched__*` to the hub bucket; `summarize_data()` in every country pipeline reads it (config `metadata.fishbase.taxa_enriched.file_prefix`) to build `taxa_traits`. Renaming a column there empties the dashboard's vulnerable-species and size views.
- **API landings schema**: column names and order in the `trips-*` parquet are agreed across all four country pipelines (`export_api_raw/validated`), declared in `peskas-api` (`schema/field_metadata.py`), and hard-coded by `peskas-validation` data-explorer lessons (`data-explorer/*.qmd`); its downloads (`lib/download.js`, `lib/peskas-api.js`) hard-code the filter/scope parameters. A column change touches all three. Kenya's KEFS catch rows are a species sample: they do not sum to `tot_catch_kg`.
- **API district-months**: `export_portal()` in `peskas.coasts` (`api_district_months()`, >= 4.24.0) writes one row per district and month to `{country}/aggregated/` in the API bucket, keyed by `gaul_2_code`, with both methods' estimates and the ARTFISH relative errors (API only). `peskas-api` (>= 1.7.0) serves it at `/data/district-months`; both repos' tests pin its 23 columns (`field_metadata.py`), so a column change touches both. `peskas-validation` (>= 2.11.0) requests it with `dataset=district-months` and only `country` and `gaul_2`; it sends a user's district list as a comma-separated `gaul_2` to both endpoints, which needs `peskas-api` >= 1.8.0.
- **Timor Dataverse release**: `upload_dataverse()` in `peskas.timor.data.pipeline` publishes Timor's `trips-validated` table as `timor_landings.csv` to Harvard Dataverse each month with a README built from `peskas-api`'s `/metadata/landings`: a description change there reaches the public dataset at the next release, and a column missing from `field_metadata.py` stops it.
- **Kenya app DB**: Mongo `app[-dev]` collections written by `peskas.kenya.data.pipeline` are read by `peskas.kenya.bmu.dashboard` schemas in `packages/nosql`.
- **Coasts portal data**: two daily workflows in `coasts` fetch from Mongo `portal` (the production `coasts_portal` database, not `portal-prod`) the collections `wio_gaul1/2`, `metrics_gaul1/2` written by `export_geos()`, and from the `peskas-coasts` bucket the latest `pds-fishing-grounds__*`, `pds-h3-effort-r9__*` (`export_pds_spatial()`) and `frame-gears__*` (`export_frame_data()`) files, then commit JSON to `public/data/`, which redeploys the site. Renaming a collection, column or file prefix in `peskas.coasts` breaks the portal at its next fetch. Money values arrive in USD, converted in `export_geos()`.
- **Timor public bucket**: `portal-*.json` in `public-timor` is fetched by `peskas.timor.portal.v2/scripts/fetchData.js`.

## Domain terms

- **PDS**: Pelagic Data Systems, solar GPS trackers on boats; the source of tracks and trips.
- **KoBo**: KoboToolbox, where enumerators record landings.
- **WCS / WF / BA / DINAPA / Lurio / KEFS**: survey programmes or partners, each with its own KoBo form chain.
- **DINAPA**: National Directorate of Fisheries and Aquaculture, Mozambique's fisheries authority; it replaced ADNAP. Code identifiers keep `adnap`; published values and user-facing text say DINAPA.
- **Landing / trip**: one boat's fishing trip as recorded at the landing site; the core row across pipelines.
- **GPS tracker method / FAO ARTFISH method**: the two ways catch and revenue are raised to the whole fleet. The first multiplies census boats by trips per GPS-tracked boat and catch per trip, each boat and gear group weighted by its share of the census boats (`estimated_*`); the second is FAO's ARTFISH: census boats × days fished as fishers report them × catch per trip, by boat and gear group (boat type alone in Mozambique) (`estimated_*_fao`).
- **Enumerator**: the person recording landings.
- **GAUL**: FAO administrative boundaries used for regional aggregation (`wio_gaul1/2`).
