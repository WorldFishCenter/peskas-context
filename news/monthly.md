# Monthly Peskas News & Updates

Write the month's "News & Updates" bulletin about Peskas and publish it as a private Artifact for the Peskas team to review. The team decides later whether and where to share it. Stay read-only on every repo: no edits to tracked files, commits, pushes, issues or pull requests, and nothing posted anywhere else (website, blog, Slack, email).

## Readers

People in the fisheries sector who are not developers: fisheries agencies and ministries, NGOs, international agencies, partners and funders. They want to know what changed in Peskas, what it lets them see or do, and how it fits Peskas's purpose: turning what small-scale fishers land into checked, open figures (catch, value, fishing activity) that agencies and communities can act on.

## 1. Period and edition

The edition covers the previous calendar month in UTC: from the 1st at 00:00 to the 1st of the run month at 00:00. Its number is `(year - 2026) * 12 + month - 8` for the month covered (September 2026 is No. 1).

## 2. Gather what shipped

The repos are checked out side by side. Two have other folder names than their public ones: `peskas.zanzibar.validation` is the Peskas Management Platform and `peskas.dashboard.app` is the country dashboards. Read `peskas-context/plugin/context/ecosystem.md` first for what each repo is and its public name.

In every repo, on the branch that is checked out:

- **NEWS.md**: take the lines added during the period: `git diff $(git rev-list -1 --before=<start> HEAD) $(git rev-list -1 --before=<end> HEAD) -- NEWS.md`.
- **Confirm each entry shipped in the period.** Match its version to a tag created in the period (`git fetch --tags --quiet`, then `git tag --sort=creatordate --format='%(creatordate:short) %(refname:short)'`). Repos with no version tags (`coasts`, `peskas.timor.portal.v2`, `peskas.show`) deploy from their default branch: confirm with the commits in the period that changed the code the entry describes, not only NEWS.md. An entry written in the period about work shipped earlier is not news: in September 2026, `coasts` NEWS gained a block describing map layers built between May and July. A reorganised NEWS file can also show old entries as added; skip them.
- **Repos without NEWS.md** (`peskas.timor.portal.v2`, `peskas.show`): read the commit subjects in the period. Ignore automated data refreshes.
- `peskas.show` (the public website) is a source for how Peskas describes itself and its partners. A change to the site counts only when it adds something for readers, such as a new country. Do not link to blog posts.

## 3. Choose what to tell

Count a change when someone outside the team would notice it or rely on it: something new to see or do on a dashboard, portal, app or the API; new data, countries, partners or languages; published figures that moved; a new link to another system or dataset; checks or privacy and security changes that affect what users get. Leave out refactors, dependencies, CI, tests, documentation-only changes, code moved between repos, automated data refreshes and anything not yet released.

- The same change released in several repos (for example the same fix in all four country pipelines) is one item, "in all four countries".
- Lead with the change that matters most to users and partners. GPS trackers are one data source among several: don't make them the lead unless nothing else happened.
- Published figures that moved go in "Figures that changed", with the size of the change and the reason, even when the story also mentions them.
- **Quiet month.** When nothing qualifies, publish the quiet edition: the headline "A quiet month for Peskas", a standfirst that says plainly that no change reached users this month, the data-flow map (it shows "No updates" everywhere by itself) and the footer. When only one or two small changes qualify, use the same headline and put them under "Also this month". Never pad a month with internal work.

## 4. Write

Match the voice of `peskas.show/posts/dashboard-upgrade.md`: plain, descriptive, professional, the team speaking as "we" where an actor is needed. Every edition frames its news within what Peskas is for, without selling it.

- Every sentence must come from a NEWS entry, a commit, or the public website. Copy numbers exactly. No forecasts, no claims of impact the sources don't make, no adjectives that praise.
- Public names only: Peskas Zanzibar, Peskas Kenya, Peskas Mozambique (the country dashboards), Peskas Timor-Leste, Peskas Coasts, Peskas Tracks, Peskas Kenya BMU dashboard, Peskas Management Platform, Peskas Fishery Data API. No function, file, column, package or repo names and no version numbers. Explain a term in a few words the first time (for example "enumerators, who record landings at the landing sites").
- Name partners in full at first mention: Wildlife Conservation Society (WCS), Kenya Fisheries Service (KEFS), Zanzibar Fisheries and Marine Resources Research Institute (ZAFIRI), Mozambique's National Directorate of Fisheries and Aquaculture (DINAPA), Timor-Leste's Ministry of Agriculture and Fisheries (MAF).
- Narrative paragraphs, not bullet lists. Lengths: standfirst 60 to 90 words; lead story 180 to 280; other stories 100 to 200; "Also this month" items one or two sentences; the whole edition under about 1,300 words.
- Then run the `humanizer` skill over all the prose, with the voice sample above. If the skill is not available, check by hand that the text has no "not X but Y" contrasts, no one-line closing sentences, no em or en dashes, no forced lists of three, no bold labels, and none of the words crucial, key (as an adjective), robust, seamless, enhance, empower, leverage, showcase, vibrant, pivotal.

## 5. Build the page

Copy `peskas-context/news/template.html` to a new file named `YYYY-MM.html` outside the repos (for example `/tmp/news/2026-10.html`). Fill only its SLOT parts, following the comment above each, then delete the SLOT comments. Keep the style, icons, logo, data-flow map, footer and script exactly as they are. `peskas-context/news/editions/2026-09.html` is a finished edition to compare with.

Before publishing, check that:

- no placeholder is left: `grep -nE 'SLOT|HEADLINE|STANDFIRST|PARAGRAPH|COUNTRY|PLATFORM|FIGURE|STEP|MONTH|YEAR|No\. N' <file>` prints nothing;
- every `data-stages` value is one or more of `collect check estimate share show`;
- every link answers 200: `curl -s -o /dev/null -w '%{http_code}' -L --max-time 15 <url>`. Remove a link that fails.

## 6. Publish and report

Publish the file with the Artifact tool as a new private artifact: title `Peskas News & Updates, <Month> <YYYY>`, icon `news`, and a one-sentence description of the month. If the Artifact tool is not available, do not publish anywhere else: say so, and give the report below so the edition can be built locally.

End the run with a short report for the reviewer:

1. The artifact link.
2. Each item included, with its sources (repo, version or commit, date).
3. Changes a reviewer might expect but you left out, one line each with the reason.
4. Any statement you could not trace to a source. There should be none; if there is one, remove it from the edition before publishing.
