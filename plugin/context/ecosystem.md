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
tracks-explorer ─► Mongo portal-* catch-events ─► peskas.coasts (fisher stats)
peskas.coasts ─► Mongo portal + GCS peskas-coasts ─► daily JSON commit to public/data/ ─► coasts portal
Timor only ─► GCS public-timor ─► peskas.timor.portal.v2
Timor only ─► peskas-api-* bucket + peskas-api /metadata ─► Harvard Dataverse (monthly, one versioned dataset)
coasts::export_portal (Timor: then export_api_district_months) ─► peskas-api-* bucket <country>/aggregated/ ─► peskas-api /data/district-months ─► peskas-validation
Kenya only ─► Mongo app[-dev] ─► peskas.kenya.bmu.dashboard
peskas.coasts ─► Airtable frame collection_stats (weekly)
```

Timor on the coasts portal (`export_portal`) is separate from `peskas.timor.portal.v2` (`public-timor`); changing one does not update the other.

## Domain terms

- **PDS**: Pelagic Data Systems, solar GPS trackers on boats; the source of tracks and trips.
- **KoBo**: KoboToolbox, where enumerators record landings.
- **WCS / WF / BA / DINAPA / Lurio / KEFS**: survey programmes or partners, each with its own KoBo form chain.
- **DINAPA**: National Directorate of Fisheries and Aquaculture, Mozambique's fisheries authority; it replaced ADNAP. Code identifiers keep `adnap`; published values and user-facing text say DINAPA.
- **Landing / trip**: one boat's fishing trip as recorded at the landing site; the core row across pipelines.
- **GPS tracker method / FAO ARTFISH method**: the two ways catch and revenue are raised to the whole fleet. The first multiplies census boats by trips per GPS-tracked boat and catch per trip, each boat and gear group weighted by its share of the census boats (`estimated_*`); the second is FAO's ARTFISH: census boats × days fished as fishers report them × catch per trip, by boat and gear group (boat type alone in Mozambique) (`estimated_*_fao`).
- **Enumerator**: the person recording landings.
- **GAUL**: FAO administrative boundaries used for regional aggregation (`wio_gaul1/2`).
