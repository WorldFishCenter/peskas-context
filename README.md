# peskas-context

The shared [Claude Code](https://code.claude.com) setup for the Peskas repos. It makes Claude work the same way for everyone, whichever Peskas repos you work on.

## What you get

- **The Peskas rules and ecosystem context** in every Claude Code session: how to work, which repos exist, how data flows between them, and which cross-repo contracts a change can break. R pipeline conventions are added in R package repos only.
- **`/peskas:check`**: reviews your changes before a pull request, including what they could break in other repos.
- **`peskas:scout`**: an agent that finds who reads a name across the Peskas repos, or how the sibling pipelines already do a step. Claude calls it on its own; you can also type `@agent-peskas:scout`.
- **[ponytail](https://github.com/DietrichGebert/ponytail)**, which keeps changes small. It is enabled by the repos, not by this plugin.

## Getting it

Nothing to install by hand. Every Peskas repo lists this plugin in its `.claude/settings.json`:

1. Open any Peskas repo in Claude Code and trust the folder. Accept the plugin install when asked.
2. Run `/plugin`, open **Marketplaces**, select `peskas` and choose **Enable auto-update**, so changes reach you automatically.

**To turn ponytail off**, add this to your own `~/.claude/settings.json`:

```json
{ "env": { "PONYTAIL_DEFAULT_MODE": "off" } }
```

## Changing it

Edit the files and push to `main`. Everyone with auto-update gets the change at their next session; there is no version to bump.

| File | What it holds |
|---|---|
| `plugin/context/rules.md` | The Peskas rules and the working style |
| `plugin/context/ecosystem.md` | Repo map, public names, data flow, cross-repo contracts, terms |
| `plugin/context/r-pipelines.md` | Conventions for coasts and the country pipelines |
| `plugin/skills/check/SKILL.md` | `/peskas:check` |
| `plugin/agents/scout.md` | `peskas:scout` |
| `plugin/hooks/hooks.json`, `plugin/scripts/context.sh` | Load the context files into each session and subagent |

Keep each context file under 10,000 characters: Claude Code shortens anything longer to a preview. Check before pushing with `claude plugin validate .`.

Repo-specific detail belongs in each repo's own `CLAUDE.md`, not here.
