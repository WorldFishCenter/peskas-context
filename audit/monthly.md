# Monthly Peskas audit

A read-only audit of the Peskas repos' Claude Code setup and READMEs. Read, run read-only commands, and report. Leave every file as it is: no edits, commits, pushes, issues or pull requests.

The repos are checked out side by side, each on its default branch. The reference for this audit is `peskas-context/plugin/context/`: `rules.md` (the Peskas rules), `ecosystem.md` (repo map, public names, data flow, cross-repo contracts) and `r-pipelines.md` (R conventions). Read all three first. Two repos have a different folder name in `ecosystem.md`: `peskas-validation` is checked out as `peskas.zanzibar.validation`, and `peskas.dashboard` as `peskas.dashboard.app`.

In every repo, check `CLAUDE.md`, `.claude/rules/*.md`, `.claude/settings.json` and `README.md` (`README.Rmd` too in the R repos) against the code. Check the three context files against the code of the repos they describe.

1. **Stale facts**: a path, function, env var, collection, bucket, file prefix, command, workflow name or schedule, version or URL that no longer matches the code. Give the doc's `file:line` and the contradicting code's `file:line`. Check public URLs with `curl -s -o /dev/null -w '%{http_code}' -L --max-time 15 <url>`.
2. **README drift** (R repos): text in `README.md` that `README.Rmd` would not render, or the reverse.
3. **Changes without doc updates**: run `git log --since='35 days ago' --stat` in each repo and flag commits that changed code a doc line describes, where that line was not updated. A commit that renamed a collection, column, file prefix, config key or env var without updating `ecosystem.md` counts.
4. **Cross-repo contracts**: for every contract in `ecosystem.md` "Cross-repo contracts", read the producer and the consumer code and flag any side that no longer matches the other.
5. **Setup consistency**: every repo's `.claude/settings.json` registers the `peskas` and `ponytail` marketplaces and enables `peskas@peskas` and `ponytail@ponytail`; every file in `peskas-context/plugin/context/` is under 10,000 characters (`wc -m`).
6. **Public names and contact** across READMEs, as listed in `ecosystem.md` under "Repo map".
7. **NEWS**: entries added in the last 35 days that name a function, file, column or package, or that a non-technical reader would not follow (rule 3 in `rules.md`).

Report findings grouped by repo, most important first. For each, give `file:line`, what is wrong, the evidence, and a one-line proposed fix. Report only real mismatches, not style preferences. End with the repos that had no findings. Keep the report under about 800 words.
