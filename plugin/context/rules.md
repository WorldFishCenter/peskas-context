# Peskas: how to work

## The Peskas rules

IMPORTANT: these apply to every change in every Peskas repo.

1. **Blast radius first.** Before editing, list what the change touches that another repo or service reads: a function other repos call, a config key coasts reads, a column, collection, file prefix, env var or API field. Find each consumer in `../<repo>` using "Data flow" and "Cross-repo contracts" in the Peskas ecosystem context, and read it; hand this search to the `peskas:scout` agent. A consumer whose repo you have not cloned cannot be checked locally: say so. The change is done when every consumer still works or changes with it in the same piece of work.
2. **Clone what already works.** Before writing code, search this repo, `../peskas.coasts/R/` and the sibling repos for code that already does the job. In the country pipelines, the fix for a broken step is usually the same step from a sibling pipeline where it works: copy it and change only names and config (`peskas:scout` compares the siblings for you). Pipelines converge, so follow the shape the siblings use and name the siblings that need the same change (`grep -rn "fn_name <-" ../peskas.*.data.pipeline/R`). Shared logic belongs in coasts; a second copy in a country repo is a signal to move it there. Write new code only when nothing exists.
3. **One-line comments, plain NEWS.** A comment says *why*, in one line where possible and never more than 2-3 sentences; code that is clear gets none, and comments never narrate the code or its history. A NEWS or changelog entry tells a non-technical reader what changed for users or data in one short line, with no function, file, column or package names.
4. **Write it the framework's documented way.** Code that follows its framework's official documentation stays readable for outside developers and AI tools. Before adding a pattern, check how the official docs do it for the version the repo uses (`DESCRIPTION`, `package.json`, `pyproject.toml`), and search the web for the current docs rather than relying on memory: for example R Packages (r-pkgs.org) and the tidyverse style guide for R, ui.shadcn.com for shadcn/ui, react.dev, nextjs.org and fastapi.tiangolo.com. This complements the repo's own logic, structure and style: follow those first, let the official docs decide where the repo is silent or inconsistent, and leave working code that predates a standard alone unless the task is about it.

End every reply that changes code with one line: `Blast radius: <consumers checked, or "nothing outside this repo">. Reused: <what you cloned, or where you looked and found nothing>.`

## Working style

Applies to every Peskas repo. For trivial tasks, use judgment.

1. **Think before coding.** State assumptions. When a request has several readings, name them and ask rather than pick silently. When something is unclear, stop and say what is confusing. When a simpler approach exists, say so.
2. **Simplicity first.** Write the minimum code that solves the problem: only the features asked for, no abstraction for single-use code, no unrequested configurability, no error handling for impossible cases. If 200 lines could be 50, rewrite it.
3. **Surgical changes.** Every changed line traces to the request. Match the existing style; leave adjacent code, comments and formatting as they are. Remove only the orphans your change created; mention unrelated dead code instead of deleting it.
4. **Goal-driven execution.** Turn the task into a checkable goal (a failing test that then passes, a check before and after a refactor) and loop until it is verified. For multi-step work, state a short plan with a check per step.
5. **Docs move with the code.** A change that makes a line in CLAUDE.md, `.claude/rules/`, a README or the Peskas context (the `peskas-context` repo) false updates that line in the same change. Prefer pointing to the file that holds a fact over restating it.

## Working across repos

- **Commit messages**: sentence-style subjects that state the outcome ("A device leaving the country deleted its whole trip history"). A fix applied to every pipeline gets the same message in each repo.
- **Per-repo detail**: each repo's own `CLAUDE.md` and `.claude/rules/` cover its internals. `peskas.timor.data.pipeline/.claude/rules/` is the most complete reference for storage, PDS, taxa and validation semantics.
