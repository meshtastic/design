# Writing style

This applies to everyone writing in this repo, human or agent: issues, pull requests, commit messages, and the docs under `standards/` and `styleguide/`.

Keep it short and plain. Say what the problem is and what changed, in ordinary words. No invented jargon, no dramatized debugging stories, no bold-lead bullet lists that read like marketing. If there's nothing worth saying, say nothing.

## Markdown

Use American spelling: color, gray, meter, favorite.

Don't hard-wrap. One line per paragraph and per bullet. Hard wrapping at 80 or 100 columns renders as ragged mid-sentence breaks inside list items on GitHub.

Don't lead bullets with a bold label. `- **Thing** — explanation` reads like a marketing deck. Write prose, or use plain bullets where the content is genuinely a list.

Prefer plain headings and prose over `> [!NOTE]` callouts, emoji in headings, and tables that hold one row.

## Alignment issues

Issues titled `[ALIGNMENT]: ...` follow a fixed shape. Match it instead of inventing your own:

- `## Decision` — what clients must do, stated once, up front.
- `## Context` — why, with links to the firmware, protocol, or client issues behind it.
- `## Required Client Behavior` — numbered prose, one item per requirement.
- `## Acceptance Criteria` — what has to be true for the work to be considered done.

Add other sections only where the spec needs them, such as a per-client tracking checklist, firmware-owned behavior, or open questions. Issues #134 and #144 are good references.

## Pull requests

Use `## Summary`, `## What changed`, `## Testing`. Say plainly when a section doesn't apply — "not applicable, documentation only" beats inventing verification.

## Commits

A short subject saying what changed. Don't add `Co-Authored-By: Claude` or "Generated with Claude Code" trailers.

## Cutting a standards version

`standards/README.md` is the entry point every other repository links to, and it names the current version, so it has to change whenever that version does. Follow the steps under "Cutting a version" on that page: add the new version file, repoint the `meshtastic_design_standards_latest.md` symlink, then update the version named at the top of the index and the row in its table.

Do all of it in the commit that adds the version. An index naming a version that is no longer current is worse than no index, because it looks authoritative.

Don't link `meshtastic_design_standards_latest.md` from anywhere on the web. GitHub serves a symlink as its target's filename, so the blob and raw views return the file name rather than the standards. Link `standards/` instead.
