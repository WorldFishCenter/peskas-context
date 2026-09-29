# peskas-context

The shared [Claude Code](https://code.claude.com) setup for the Peskas repos. With it, Claude follows the same Peskas rules and knows how the repos fit together, for everyone and in every Peskas repo.

## Install

You do this once. You need Claude Code installed.

**1. Open a Peskas repo in Claude Code.** Pull the latest version of any Peskas repo you work on, open a terminal in it and run `claude`. If Claude Code asks whether you trust the folder, answer yes.

**2. Close Claude Code and open it again.** The first session downloads the setup in the background; from the second session on it is active.

**3. Check it works.** Type `/peskas:check`. If it appears in the suggestions, you are done.

**4. Turn on automatic updates.** Type `/plugin`, open **Marketplaces**, select **peskas** and choose **Enable auto-update**.

## Using it

- **Nothing to do day to day.** The Peskas rules and ecosystem context load by themselves in every session.
- **Before a pull request**, type `/peskas:check`. It reviews your changes, including what they could break in other Peskas repos.
- **To find who uses something across the repos**, ask `@agent-peskas:scout`, for example: `@agent-peskas:scout who reads the taxa_summaries collection?`. Claude also calls it by itself when needed.

The repos also turn on [ponytail](https://github.com/DietrichGebert/ponytail), which keeps changes small. To turn it off, add this to your own `~/.claude/settings.json`:

```json
{ "env": { "PONYTAIL_DEFAULT_MODE": "off" } }
```

## If `/peskas:check` does not appear

- Type `/plugin marketplace update peskas`, then restart Claude Code.
- Make sure the Peskas repo you opened is up to date: its `.claude/settings.json` must list `peskas@peskas`.

## Changing the setup

Edit the files below and push to `main`. Everyone with automatic updates gets the change in their next session; there is no version number to change.

| File | What it holds |
|---|---|
| `plugin/context/rules.md` | The Peskas rules and working style |
| `plugin/context/ecosystem.md` | Repo map, public names, data flow, cross-repo contracts, terms |
| `plugin/context/r-pipelines.md` | Conventions for coasts and the country pipelines (loaded in R repos only) |
| `plugin/skills/check/SKILL.md` | `/peskas:check` |
| `plugin/agents/scout.md` | `peskas:scout` |
| `plugin/hooks/hooks.json`, `plugin/scripts/context.sh` | Load the context files into each session |
| `audit/monthly.md` | Instructions for the monthly read-only audit, which runs as a Claude Code routine |

Before pushing, run `claude plugin validate .` and keep each file in `plugin/context/` under 10,000 characters; Claude Code cuts longer ones to a preview. Keep the name `peskas` in `.claude-plugin/marketplace.json` and `plugin/.claude-plugin/plugin.json` unchanged: every install depends on it.

Details about a single repo belong in that repo's own `CLAUDE.md`, not here.
