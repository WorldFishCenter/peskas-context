# Check one country's portal-prod collections against portal.odcs.json, read-only.
#
#   cd ../peskas.kenya.data.pipeline   # or zanzibar, mozambique
#   Rscript ../peskas-context/dictionary/prod_check.R
#
# Reads the pipeline's own .env and inst/config.yml (production) and stops unless the
# database is portal-prod. For each collection in the contract: its columns, the measure
# names it carries, and no two rows at the same grain. Exit 1 on any mismatch.

suppressMessages(dotenv::load_dot_env(".env"))
conf <- config::get(config = "production", file = "inst/config.yml")
db <- conf$storage$mongodb$databases$dashboard$database_name
stopifnot(db == "portal-prod")
url <- conf$storage$mongodb$connection_strings$main

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
contract <- jsonlite::read_json(file.path(here, "portal.odcs.json"))

problems <- character()
for (collection in contract$schema) {
  name <- collection$physicalName
  m <- mongolite::mongo(name, db = db, url = url)
  props <- collection$properties
  fields <- vapply(props, `[[`, "", "name")
  meta <- m$find('{"type":"metadata"}', fields = '{"columns":1,"timestamp":1,"_id":0}')
  columns <- if (nrow(meta)) unlist(meta$columns) else character()
  if (!setequal(columns, fields)) {
    problems <- c(problems, sprintf(
      "%s: columns %s, contract %s", name, toString(sort(columns)), toString(sort(fields))
    ))
  }

  keys <- Filter(function(p) isTRUE(p$primaryKey), props)
  keys <- vapply(keys[order(vapply(keys, `[[`, 0, "primaryKeyPosition"))], `[[`, "", "name")
  grain <- paste0('{', paste(sprintf('"%s":"$%s"', keys, keys), collapse = ","), '}')
  dup <- m$aggregate(sprintf(
    '[{"$match":{"type":{"$ne":"metadata"}}},{"$group":{"_id":%s,"n":{"$sum":1}}},{"$match":{"n":{"$gt":1}}},{"$count":"groups"}]',
    grain
  ))
  if (nrow(dup)) problems <- c(problems, sprintf("%s: %d groups of rows share a grain", name, dup$groups))

  measured <- Filter(function(p) !is.null(p$enum), props)
  if (length(measured)) {
    field <- measured[[1]]$name
    declared <- vapply(measured[[1]]$enum, `[[`, "", "value")
    found <- unlist(m$distinct(field, '{"type":{"$ne":"metadata"}}'))
    if (!setequal(found, declared)) {
      problems <- c(problems, sprintf(
        "%s: %s in the data only: %s; in the contract only: %s", name, field,
        toString(setdiff(found, declared)), toString(setdiff(declared, found))
      ))
    }
  }
  cat(sprintf("%-20s %7d rows, written %s\n", name, m$count() - 1,
              if (nrow(meta)) format(unlist(meta$timestamp)[1]) else "?"))
}

listed <- vapply(contract$schema, `[[`, "", "physicalName")
others <- setdiff(mongolite::mongo(db = db, url = url)$run('{"listCollections":1,"nameOnly":true}')$cursor$firstBatch$name, listed)
if (length(others)) cat("Not in the contract:", toString(sort(others)), "\n")

if (length(problems)) {
  cat(paste0("PROBLEM ", problems, "\n"), sep = "")
  quit(status = 1)
}
cat("portal-prod matches the contract\n")
