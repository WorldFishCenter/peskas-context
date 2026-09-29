---
name: check
description: Review changes in a Peskas repo against the Peskas rules (blast radius, clone what works, comments and NEWS, the framework's documented way), security and docs, before a pull request or at any time.
argument-hint: "[PR number | branch | base..head | path]"
disable-model-invocation: true
context: fork
effort: high
disallowed-tools:
  - Edit
  - Write
  - NotebookEdit
allowed-tools:
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git show *)
  - Bash(git status *)
  - Bash(gh pr diff *)
  - Bash(gh pr view *)
---

Review one change in a Peskas repo and report what it breaks or violates. This is a read-only review: report findings and leave every file as it is.

Target: `$ARGUMENTS`
- Empty: commits not yet on the base branch plus all uncommitted changes, untracked files included. The base is `origin/HEAD`.
- A number: that GitHub pull request (`gh pr view`, `gh pr diff`).
- A branch or `base..head`: that range. A path: the uncommitted changes under it.

## 1. Load the rulebook

The peskas plugin loads the Peskas context into your context: the Peskas rules and working style, the ecosystem (repo map, data flow, cross-repo contracts) and, in R repos, the R pipeline conventions. If it is missing, read `${CLAUDE_PLUGIN_ROOT}/context/*.md`. Also read this repo's `CLAUDE.md` and `.claude/rules/*.md`. Together these are the rulebook: every rule finding cites the line it breaks.

## 2. Read the change

Read each changed file in full, not only the hunks. Done when every changed file is read.

## 3. Trace every consumer (rule 1, blast radius)

List each name the change adds, renames, removes or reshapes that another repo or service can see: an exported function or its arguments, a config key, an output column, a file prefix, a Mongo collection or field, a bucket path, an env var, an API route or field, a KoBo or Airtable field. The ecosystem context's "Data flow" and "Cross-repo contracts" say who produces and who consumes each one.

For each name, grep the sibling repos (`../<repo>`, listed in the ecosystem context's repo map) for its consumers and read each hit. A producer change must leave every consumer working; a consumer change must match what the producer writes today. Siblings are local clones: grep them as checked out, and note any sibling that is missing or not on its working branch. Use `.env.example` and the config files for env var names; leave `.env*`, `.Renviron` and `user-passwords-*` files closed.

Done when every listed name has its consumers found and checked, or is recorded as having none.

## 4. Look for code that already works (rule 2, clone)

For each function or non-trivial block the change adds or rewrites, grep this repo, `../peskas.coasts/R/` and the sibling repos for code that does the same job. In a country pipeline, open the same step in each sibling pipeline and compare. A new implementation where a working one exists is a finding that cites the existing `file:line`; so is a fix to one pipeline that a sibling needs too.

Done when every added function or block has its search recorded: the existing code found, or none.

## 5. Check every dimension

- **Blast radius**: the consumers from step 3, and the cross-repo contracts. A breaking change to anything a pipeline calls from coasts ships as a coasts release first (DESCRIPTION bump plus a NEWS block).
- **Clone**: the findings from step 4, and shapes that drift from the sibling pipelines (function names, config keys, workflow jobs).
- **Comments and NEWS** (rule 3): comments longer than 2-3 sentences, comments that narrate the code or its history, and comments on code that is clear; NEWS or changelog lines that name a function, file, column or package, or that a non-technical reader would not follow; a user-visible change without a `NEWS.md` entry in repos that keep one.
- **Documented way** (rule 4): new code that departs from how the framework's official docs do it for the version the repo uses. Check the docs on the web and cite the page. Report it only where the repo itself does not already settle the question.
- **Correctness**: logic errors, edge cases (empty or zero-row input, NA, time zones, duplicates), the wrong config profile or database, errors swallowed into silent success.
- **Security**: secrets in code, logs, commits or frontend bundles (`VITE_*` and `NEXT_PUBLIC_*` values are public); a whole config object logged; a `coasts::` workflow call without `log_threshold = logger::INFO`; API routes missing authentication or scoping to the caller; injection through query building.
- **Conventions**: the Peskas working style and R pipeline conventions, plus the repo's own rules: function shape and naming, column names, and edits unrelated to the change's purpose.
- **Stability and manageability**: hard-coded values that belong in config, unpinned versions, a new dependency where an installed one does the job, paths that lose or overwrite data (drop and reinsert, an empty file becoming `latest`), non-trivial logic without a check, and CI changes that skip or weaken a step.
- **Docs**: any line in CLAUDE.md, `.claude/rules/`, README (both `README.Rmd` and `README.md` in R repos) or the Peskas context that the change makes false; roxygen edits without the matching `man/` update.

Done when each dimension has findings or is listed as clear.

## Evidence bar

Each finding cites `file:line` in the change and its evidence: the rule's file and line, or the consumer's `file:line`. Drop anything you cannot cite. Report what the change introduces or makes worse. Pre-existing problems you came across go in one line each at the end, at most three.

Severity:
- **Blocker**: breaks a consumer, production data or a deploy, loses data, exposes a secret, or is wrong logic on a main path.
- **Fix**: breaks a Peskas rule, or will cost maintenance later. Breaking rule 2, 3 or 4 is at least a Fix.
- **Nit**: minor. Report at most five; count the rest.

## Report

Keep it under about 600 words:

```
Verdict: Ready for PR | Fix N blockers first | Fixes recommended
Reviewed: <target>, base <ref>, <N> files

Blockers
1. path:line — what breaks, and where (consumer path:line). Fix: <one line>
Fixes
Nits
Clear: <dimensions with no findings>
Not checked: <missing or stale siblings, anything you could not verify>
Pre-existing: <at most three lines>
```
