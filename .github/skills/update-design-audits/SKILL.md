# Skill: Update Design Audit Files

## When to use this skill

Use this skill when asked to update the cross-platform design audit documents in `standards/audits/` with recent pull request activity from the `meshtastic/Meshtastic-Apple` and/or `meshtastic/Meshtastic-Android` repositories. Typical triggers:

- "Update the audit files with the last N days of PRs"
- "Refresh the audits"
- Anything mentioning `[ALIGNMENT]` tags — those are the highest priority

---

## The Four Audit Files

All files live under `standards/audits/` in the `meshtastic/design` repository.

### 1. `menu-alignment-audit.md`
Tracks cross-platform navigation surface alignment (tab order, context menus, node detail views, etc.). Each section that has active work includes a **Tracking** table listing the GitHub issues and, once resolved, the merged PRs.

**What to update:**
- When a tracking issue is closed by a merged PR, add a `PR` column and `Status` column to the tracking table and mark `✅ Merged YYYY-MM-DD`.
- Check the PR title and linked issue number to confirm it resolves the specific section.
- PR titles for this file typically contain: `[ALIGNMENT]`, `tab`, `navigation`, `context menu`, `node list`, `rename`, `reorder`.

### 2. `settings-validation-matrix.md`
Tracks which settings screens and fields exist on each platform, along with validation constraint alignment. Sources are in `standards/audits/data/`.

**What to update:**
- **§1 Screen Coverage tables** — when a screen or field is added to a platform, change `❌` to `✅` and add a PR link/note.
- **§2 Screens Only on Android** — when Apple adds a previously Android-only screen, add `— ✅ Now on both platforms` to the section header and note the Apple PR.
- **§3 Field-level mismatches** — when a gap is closed, update the Discrepancy column to `✅ Fixed` with the PR link and date.
- **§4 Discrepancy Summary** — strike through resolved rows using `~~text~~` and add PR reference.
- **§5 Deprecated field handling** — Items in §5.7 summary matrix: when an item is resolved, change `❌` / `⚠️` to `✅ Fixed (PR #XXXX)`.
- Update **Last Updated** date at the top of the file.
- PR titles for this file typically contain: field names (`compass_orientation`, `air_quality`, `ntp_server`), `config`, `validation`, `missing fields`.

### 3. `cross-platform-spec-audit.md`
Tracks SpecKit feature specifications across both platforms — what's specced, in-progress, or implemented.

**What to update:**
- **Feature Specification Matrix** — when a feature's status changes (Draft → Implemented, In Progress → Implemented), update the status cell with the merged PR link and date.
- **Cross-Platform Gaps** — when a gap is closed (e.g. a spec is written for the missing platform), strike through the row with `~~text~~` and note `✅ Gap closed — PR #XXXX`.
- **"Features nearing merge" table** — remove rows for features that have now merged to main.
- Update **Last Updated** date at the top.
- PR titles for this file typically contain: spec names (`TAK v2`, `M3 Expressive`, `message formatting`, `lockdown`), `spec`, `SpecKit`.

### 4. `community-alignment-matrix.md`
Maps open design repo issues against community opinion and Design Standards v1.4. 

**What to update:**
- Update the **Date** header at the top.
- For issues where implementation PRs have merged, add a note to the relevant row with the PR links and what was resolved.
- Update **Key Takeaways** bullet points for issues that have had significant progress.
- Do not close or remove issues from the matrix unless the design issue itself is closed.
- PR titles for this file typically mention issue numbers or topic areas that match issue descriptions.

---

## Step-by-Step Update Process

### 1. Create a branch

```bash
git checkout -b audits/YYYY-MM-update
```

Always work on a branch — never commit directly to master.

### 2. Fetch recent PRs from both repos

```bash
# Apple PRs (last 30 days)
gh pr list --repo meshtastic/Meshtastic-Apple \
  --state merged --limit 80 \
  --json number,title,mergedAt,body | \
  jq '.[] | select(.mergedAt > "YYYY-MM-DDT00:00:00Z")'

# Android PRs (last 30 days)
gh pr list --repo meshtastic/Meshtastic-Android \
  --state merged --limit 100 \
  --json number,title,mergedAt | \
  jq '.[] | select(.mergedAt > "YYYY-MM-DDT00:00:00Z")'
```

Replace `YYYY-MM-DD` with the date 30 days ago.

### 3. Categorize PRs by audit file

Scan each PR title and sort into buckets:

| Keyword(s) in title | Likely affects |
|---------------------|---------------|
| `[ALIGNMENT]`, `tab`, `navigation`, `context menu`, `reorder`, `rename tab` | menu-alignment-audit.md |
| `config`, `validation`, `missing field`, field name (e.g. `compass_orientation`, `ntp_server`, `air_quality`) | settings-validation-matrix.md |
| `spec`, `SpecKit`, feature name (`TAK v2`, `M3 Expressive`, `lockdown`) | cross-platform-spec-audit.md |
| Issue numbers `#83`, `#99`, `#100`, unit/locale, translate, measurement | community-alignment-matrix.md |

When a PR title is ambiguous, run:
```bash
gh pr view PRNUM --repo meshtastic/Meshtastic-Apple
```
to read the body and linked issues.

### 4. For each relevant PR, determine the specific change

For settings PRs, read the PR body or diff to identify:
- Which screen was changed
- Which specific fields were added/fixed/removed
- What the new constraint/validation is

For alignment PRs, confirm:
- Which audit section the PR addresses (§1, §3, etc.)
- The exact issue number the PR closes

### 5. Edit the audit files

Apply changes using the patterns described in each file's section above. Key conventions:
- Use `✅` for resolved/implemented
- Use `⚠️` for partial or platform-conditional
- Use `❌` for missing/broken
- Use `~~strikethrough~~` for items that are no longer applicable
- Always include a PR link: `[#1234](https://github.com/meshtastic/Meshtastic-Apple/pull/1234)`
- Always include the merge date: `(YYYY-MM-DD)`

### 6. Commit and push

```bash
git add standards/audits/
git commit -m "audits: MONTH YEAR update — summary of changes

[ALIGNMENT] menu-alignment-audit: (if changed)
- §N: mark resolved — Apple PR #XXXX, Android PR #XXXX

settings-validation-matrix:
- Last Updated: YYYY-MM-DD
- (bullet each changed row)

cross-platform-spec-audit:
- (bullet each changed cell)

community-alignment-matrix:
- Date: MONTH DD, YYYY
- (bullet each updated issue)"

git push -u origin audits/YYYY-MM-update
```

### 7. Create a PR

```bash
gh pr create \
  --repo meshtastic/design \
  --base master \
  --title "audits: MONTH YEAR update — Apple/Android PRs" \
  --body "Updates all 4 audit files in \`standards/audits/\` based on PR activity from the last 30 days.

## Changes
### menu-alignment-audit.md
- ...

### settings-validation-matrix.md
- ...

### cross-platform-spec-audit.md
- ...

### community-alignment-matrix.md
- ..."
```

---

## Important Conventions

### `[ALIGNMENT]` tag
Any PR or issue marked `[ALIGNMENT]` in its title/label tracks cross-platform UX parity work. These are highest priority to capture in the audit. Always update `menu-alignment-audit.md` and the relevant field/screen rows in `settings-validation-matrix.md`.

### Status marker cheat sheet

| Symbol | Meaning |
|--------|---------|
| `✅` | Present/implemented/fixed on this platform |
| `⚠️` | Present but with known issues or partial implementation |
| `❌` | Missing or broken on this platform |
| `🔴 Branch Complete` | Spec/feature complete on branch, awaiting merge |
| `🔵 In Progress` | Implementation underway, tasks partially done |
| `🔵 Draft` | Spec written, implementation not started |
| `~~text~~` | Struck through — no longer applicable, resolved, or removed |

### Linking format

Always use inline markdown links:
```
✅ **Fixed** in Apple PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847) (2026-05-21)
```

### Data files

The detailed per-platform validation references live in `standards/audits/data/`:
- `settings-validation-android.md` — Android validation rules per screen/field
- `settings-validation-apple.md` — Apple validation rules per screen/field

When an Android or Apple validation rule changes, update the appropriate data file **and** the matrix.

---

## Reference: Repo URLs

| Resource | URL |
|----------|-----|
| Apple repo | https://github.com/meshtastic/Meshtastic-Apple |
| Android repo | https://github.com/meshtastic/Meshtastic-Android |
| Design repo | https://github.com/meshtastic/design |
| Design standards (latest) | `standards/meshtastic_design_standards_latest.md` |
