# Alignment dashboard

Builds the cross-platform alignment coverage page from the issues in this
repository. Published by `.github/workflows/alignment-dashboard.yml`.

## Why it reads issue bodies as well as sub-issues

Alignment work is tracked two ways here and neither covers everything. Of the
24 open topics, 11 track platforms only in a `## Platform Tracking` list in the
issue body, 5 only through native sub-issues, and 8 through both. Issue bodies
also reach repositories the sub-issue graph never does, such as `device-ui` and
`meshtastic-site-planner`. Reading only one source would leave the newest specs
looking empty.

Where the two disagree, the API wins and the disagreement is reported rather
than silently resolved, because the checkbox is maintained by hand and drifts.

## Running it locally

```shell
cd tools/alignment-dashboard
python3 -m unittest discover -s tests
python3 generate.py --out site/data.json
python3 -m http.server -d site 8000
```

The generator uses `GITHUB_TOKEN` if it is set and falls back to `gh auth
token`, so it runs the same way locally as it does in Actions. A full refresh
is two or three GraphQL requests, around 35 points of the 5000 per hour budget.

`refs-cache.json` maps a reference to whether it is an issue or a pull request.
That never changes for a given number, so the cache is permanently valid and
steady-state runs only look up references they have not seen.

## Files

- `parser.py` — extracts tracking rows from issue bodies. No network, so the
  tests run against fixtures copied verbatim from real issues.
- `generate.py` — fetches the issue graph, resolves references, reconciles the
  two sources and writes `data.json`.
- `platforms.json` — platform names, aliases and the tracking headings to read.
  Extend this rather than the code when a new spelling appears.
- `site/` — the page. Plain HTML, CSS and JavaScript with no build step.

## Adding a platform or an alias

Add it to `platforms.json`. Rows whose label does not map are still emitted,
and each one raises a `platform_unmapped` finding naming the exact string, so
the table grows from what the issues actually say rather than from guesswork.

Set `"column": true` to give a platform its own matrix column. Sparse
platforms are better left `false`; they still appear in the topic detail, and
a column that is blank on almost every row reads as a gap that is not there.

## Colors

The palette follows section 7 of the design standards, with two deviations
that the file records inline. Green 600 is labeled there as green text on
light backgrounds but measures 2.35:1 on Neutral 50, so shipped text uses
Green 800 and Green 700 is used only for glyphs. Blue 600 measures 4.16:1 on a
Neutral 100 card, so links use Blue 700. Both hold 4.5:1 in either theme.
