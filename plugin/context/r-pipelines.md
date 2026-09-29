# Peskas R pipelines

## R pipeline conventions

Shared by `peskas.coasts` and the four active country pipelines.

- **Shared code lives in coasts.** Storage, Mongo, KoBo, Airtable and PDS helpers are called as `coasts::fn()`. Several country repos still carry local copies of coasts helpers (Airtable and KoBo validation-status functions); prefer the coasts version and flag the duplicate.
- **Config**: the `config` package with `default` and `production` profiles, values from env vars via `!expr Sys.getenv()`, `.env` loaded by `read_config()`. The file is `inst/config.yml` in country repos and `inst/conf.yml` in coasts. `production` runs only in CI on `main`; any other branch runs against `-dev` buckets and databases, which is the integration test.
- **Secrets**: the resolved config holds credentials. Log individual values you need, never the whole config object. `.env` files stay local.
- **Function shape**: `ingest_*`, `preprocess_*`, `validate_*`, `merge_*`, `export_*`. Body pattern: `read_config()` → auth → download latest → process → `logger::log_info()` → `add_version()` → upload. Each workflow step is one exported function called from `.github/workflows/data-pipeline.yaml`.
- **Column names**: refer to columns as `.data$col` or `"col"` in dplyr/tidyr code, never bare, so `R/globals.R` declares only `"."`.
- **Logging**: `logger` package. Pass `log_threshold = logger::INFO` to every `coasts::` workflow call in CI.
- **coasts reads country config**: coasts helpers read each country's `inst/config.yml` via `read_config(package = ...)`. Search `../peskas.coasts/R/` as well as the local `R/` before removing a config key.
- **Storage config**: address a provider directly (`conf$storage$google`) or use `coasts::resolve_storage_opts(conf, type)`; iterating over `conf$storage` children breaks when a provider is added.
- **Listing objects**: `coasts::cloud_object_name()` returns one name; `coasts::cloud_object_names()` enumerates. List once per function and pass the vector down; PDS buckets hold ~100k objects.
- **Taxa**: pin the FishBase/SeaLifeBase release in config and pass `conf` to `coasts::get_taxa_morphometrics()` (without it, "latest" overrides the pin). Set `metadata.fishbase.fao_areas` in every country config; coasts silently falls back to `c(51, 57)`.
- **PDS device selection**: prefer `select_by: community` or `exclude_customers`; a customer allowlist drops the history of trackers later reassigned.
- **Env values**: JSON-valued env vars (e.g. `GCP_SA_KEY`) are minified to one line, since dotenv parses line by line. `AIRTABLE_TOKEN` is the bare `pat…` value; coasts adds `Bearer `.
- **Docs**: roxygen, with `man/` committed. Run `devtools::document()` after changing roxygen comments.
- **Releases**: the top block of `NEWS.md` becomes the GitHub release. Bump `Version:` in DESCRIPTION and add a block written for non-technical readers (rule 3):
  ```
  # <pkg> X.Y.Z
  ## <one-line headline>
  * **NEW** Portal now shows monthly revenue per district.
  * **FIXED** Empty trips no longer stop the track processing.
  ```
- **CI**: each pipeline builds a GHCR image `r-runner-peskas-<country>` in a `build-container` job; every other job runs inside it. Crons differ per repo; read the workflow file rather than trusting prose.
