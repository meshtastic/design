#!/usr/bin/env python3
"""Build the alignment dashboard data file from the meshtastic/design issues.

Reads the issue graph and the tracking lists in the issue bodies, reconciles
the two, and writes data.json for the static page. Standard library only.

  GITHUB_TOKEN=... python3 generate.py --out site/data.json

Without GITHUB_TOKEN it falls back to `gh auth token`, so it runs locally the
same way it runs in Actions.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

from parser import count_checkbox_rows, load_config, parse_issue

API = "https://api.github.com/graphql"
REPO_OWNER, REPO_NAME = "meshtastic", "design"
STALE_DAYS = 30
HISTORY_DAYS = 180

ISSUE_FIELDS = """
  id number title state stateReason url updatedAt createdAt
  repository { nameWithOwner isArchived }
  assignees(first:3){ totalCount }
"""

QUERY = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    issues(first:50, after:$cursor, states:[OPEN,CLOSED]) {
      pageInfo { hasNextPage endCursor }
      nodes {
        %(fields)s
        body
        labels(first:10){ nodes { name } }
        subIssuesSummary { total completed }
        parent { number }
        subIssues(first:20) {
          totalCount
          nodes {
            %(fields)s
            subIssuesSummary { total completed }
            subIssues(first:10) { totalCount nodes { %(fields)s } }
          }
        }
      }
    }
  }
}
""" % {"fields": ISSUE_FIELDS}


def token():
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("No GITHUB_TOKEN and `gh auth token` failed.")


def graphql(query, variables, tok):
    """POST a query. Partial errors are returned, not raised: a reference to a
    deleted issue comes back as data plus an errors entry, and losing the whole
    run over one dead link would be worse than recording it."""
    payload = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(API, data=payload, headers={
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/json",
        "User-Agent": "meshtastic-alignment-dashboard",
    })
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        sys.exit(f"GraphQL HTTP {exc.code}: {exc.read()[:400].decode(errors='replace')}")


def fetch_issues(tok):
    issues, cursor = [], None
    while True:
        body = graphql(QUERY, {"owner": REPO_OWNER, "name": REPO_NAME,
                               "cursor": cursor}, tok)
        if "data" not in body or not body["data"].get("repository"):
            sys.exit(f"Unexpected GraphQL response: {json.dumps(body)[:400]}")
        page = body["data"]["repository"]["issues"]
        issues.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        cursor = page["pageInfo"]["endCursor"]


def resolve_refs(keys, tok, cache):
    """Batch aliased issueOrPullRequest lookups, grouped by repo.

    Every reference is looked up on every build. The cache is a fallback for
    lookups that fail, never a way to skip one: an issue's state is the whole
    point of this dashboard and it changes, so reusing a cached state would
    freeze every cell at whatever it happened to be the first time it was seen.
    Resolving all of them costs about one point per forty references.
    """
    fresh, by_repo = {}, {}
    for repo, number in keys:
        by_repo.setdefault(repo, []).append(number)

    for repo, numbers in by_repo.items():
        owner, name = repo.split("/", 1)
        for start in range(0, len(numbers), 40):
            chunk = numbers[start:start + 40]
            aliases = "\n".join(
                f'a{i}: issueOrPullRequest(number:{n}) {{ __typename '
                f'... on Issue {{ number title state stateReason url updatedAt '
                f'assignees(first:1){{ totalCount }} }} '
                f'... on PullRequest {{ number title state merged mergedAt url '
                f'updatedAt }} }}' for i, n in enumerate(chunk))
            query = (f'query {{ repository(owner:"{owner}", name:"{name}") '
                     f'{{ nameWithOwner {aliases} }} }}')
            body = graphql(query, {}, tok)
            repo_data = (body.get("data") or {}).get("repository") or {}
            canonical = repo_data.get("nameWithOwner", repo)
            for i, number in enumerate(chunk):
                node = repo_data.get(f"a{i}")
                fresh[f"{repo}#{number}"] = normalize_ref(node, canonical, repo)

    # A lookup that returned nothing keeps whatever the last good run knew, so
    # one deleted or briefly unreachable reference does not blank a cell.
    for key, value in fresh.items():
        if value.get("type") is None and cache.get(key, {}).get("type"):
            continue
        cache[key] = value
    return cache


def normalize_ref(node, canonical, requested):
    if not node:
        return {"type": None, "state": "unknown", "title": "", "url": ""}
    if node["__typename"] == "PullRequest":
        state = "merged" if node.get("merged") else (
            "open" if node["state"] == "OPEN" else "closed")
        return {"type": "PR", "state": state, "title": node.get("title", ""),
                "url": node.get("url", ""), "repo": canonical,
                "renamedFrom": requested if canonical != requested else None}
    if node["state"] == "OPEN":
        state = "open"
    elif node.get("stateReason") == "NOT_PLANNED":
        state = "not_planned"
    else:
        state = "completed"
    return {"type": "ISSUE", "state": state, "title": node.get("title", ""),
            "url": node.get("url", ""), "repo": canonical,
            "assigned": (node.get("assignees") or {}).get("totalCount", 0) > 0,
            "renamedFrom": requested if canonical != requested else None}


def strip_prefixes(title):
    import re
    stripped = re.sub(r"^(\s*\[[^\]]+\]\s*)+:?\s*", "", title).strip()
    return stripped or title


def iter_descendants(node, seen=None):
    """Every sub-issue below this node, at any depth, each yielded once."""
    seen = seen if seen is not None else set()
    for child in (node.get("subIssues") or {}).get("nodes", []):
        if child["id"] in seen:
            continue
        seen.add(child["id"])
        yield child
        yield from iter_descendants(child, seen)


def walk_sub_issues(node, seen, path, findings, topic_number):
    """Flatten the sub-issue tree, dropping back edges and recording truncation."""
    out = []
    for child in (node.get("subIssues") or {}).get("nodes", []):
        key = child["id"]
        if key in path:
            findings.append({
                "topic": topic_number, "type": "cycle", "severity": "warning",
                "message": f"{child['repository']['nameWithOwner']}#{child['number']} "
                           "is its own ancestor; the back edge was dropped.",
            })
            continue
        out.append(child)
        out.extend(walk_sub_issues(child, seen, path | {key}, findings, topic_number))
    total = (node.get("subIssues") or {}).get("totalCount", 0)
    got = len((node.get("subIssues") or {}).get("nodes", []))
    if total > got:
        findings.append({
            "topic": topic_number, "type": "truncated", "severity": "warning",
            "message": f"Issue {node['number']} has {total} sub-issues but only "
                       f"{got} were returned. The page is missing some children.",
        })
    return out


def cell_state(cell, rows):
    """First match wins. The API beats the checkbox, because the checkbox is
    hand-maintained and drifts; the disagreement is recorded, not resolved."""
    trackers = [e for e in cell["evidence"] if e["role"] == "tracker"]
    impls = [e for e in cell["evidence"] if e["role"] == "implementation"]
    all_checked = bool(rows) and all(r["checked"] for r in rows)

    # Checked before not_filed: a row saying this platform is out of scope is a
    # decision, not an absence, and counting it as outstanding work would mark a
    # platform down for something nobody ever expected it to do.
    if any(r["outOfScope"] for r in rows) and not trackers:
        return "not_applicable", False
    if any(r["notFiled"] for r in rows) and not trackers:
        return "not_filed", False
    if not trackers and not impls:
        # A ticked row citing nothing is a claim, not a result. It gets its own
        # state so it never lands in the shipped count: counting it there would
        # flatter whichever platform is loosest about linking its work, which
        # is the opposite of what this page is for.
        return ("claimed", True) if all_checked else ("not_filed", False)
    if trackers and all(t["state"] == "not_planned" for t in trackers):
        return "not_planned", False
    if trackers and all(t["state"] == "completed" for t in trackers):
        return "shipped", False
    if not trackers and impls and all(i["state"] == "merged" for i in impls):
        return "shipped", False
    if any(r["blocked"] for r in rows):
        return "blocked", False
    if any(t["state"] == "open" for t in trackers):
        active = [i for i in impls if i["state"] in ("open", "merged")]
        assigned = any(t.get("assigned") for t in trackers)
        return ("in_progress" if (active or assigned) else "filed_not_started"), False
    # An open pull request and no tracker issue is still work under way. Without
    # this the row falls through to unknown, which reads as a parser failure
    # rather than as the plain fact that somebody is working on it.
    if any(i["state"] == "open" for i in impls):
        return "in_progress", False
    return "unknown", False


DISAGREEMENTS = {
    "checked_but_open": "Marked done, but the linked issue is still open.",
    "checked_but_not_planned": "Marked done, but the linked issue was closed as not planned.",
    "unchecked_but_completed": "Marked open, but the linked issue is closed as completed.",
    "claimed_no_evidence": "Marked done with no issue or pull request linked, so this cannot be verified.",
    "native_missing": "Cited in the tracking list but not linked as a sub-issue.",
    "row_missing": "Linked as a sub-issue but absent from the tracking list.",
    "pr_unmerged": "The cited pull request was closed without merging.",
}


def build(issues, cfg, refs):
    platforms = {p["id"]: p for p in cfg["platforms"]}
    repo_to_platform = {r: p["id"] for p in cfg["platforms"] for r in p["repos"]}
    findings, topics = [], []
    rows_by_issue, seen_rows = {}, 0

    for issue in issues:
        rows, issue_findings = parse_issue(issue["number"], issue["body"], cfg)
        rows_by_issue[issue["number"]] = rows
        findings.extend(issue_findings)
        seen_rows += len(rows)

    for issue in issues:
        number = issue["number"]
        labels = [n["name"] for n in issue["labels"]["nodes"]]
        rows = rows_by_issue[number]
        children = walk_sub_issues(issue, set(), {issue["id"]}, findings, number)
        if not (children or rows or "alignment" in labels):
            continue

        cells = {}

        def cell_for(platform_id):
            return cells.setdefault(platform_id, {
                "evidence": [], "disagreements": [], "linkage": [],
                "aspects": [], "notes": [],
            })

        for child in children:
            platform_id = repo_to_platform.get(child["repository"]["nameWithOwner"])
            if not platform_id:
                continue
            key = f'{child["repository"]["nameWithOwner"]}#{child["number"]}'
            ref = refs.get(key, {})
            cell_for(platform_id)["evidence"].append({
                "ref": key, "sources": ["native"], "role": "tracker",
                "state": ref.get("state", "unknown"), "title": child["title"],
                "url": child["url"], "assigned": ref.get("assigned", False),
            })

        for row in rows:
            if not row["platform"]:
                continue
            cell = cell_for(row["platform"])
            if row["aspect"]:
                cell["aspects"].append(row["aspect"])
            cell["notes"].append({"checked": row["checked"],
                                  "text": row["text"][:220],
                                  "line": row["line"]})
            for index, ref in enumerate(row["refs"]):
                key = f'{ref["repo"]}#{ref["number"]}'
                meta = refs.get(key, {})
                kind = meta.get("type")
                if kind == "PR":
                    role = "implementation"
                elif index == 0 and not row["shippedIn"]:
                    role = "tracker"
                else:
                    role = "related"
                existing = next((e for e in cell["evidence"] if e["ref"] == key), None)
                if existing:
                    if "row" not in existing["sources"]:
                        existing["sources"].append("row")
                else:
                    cell["evidence"].append({
                        "ref": key, "sources": ["row"], "role": role,
                        "state": meta.get("state", "unknown"),
                        "title": meta.get("title", ""), "url": meta.get("url", ""),
                        "assigned": meta.get("assigned", False),
                        "repoInherited": ref["inherited"],
                    })

        for platform_id, cell in cells.items():
            cell_rows = [r for r in rows if r["platform"] == platform_id]
            state, unverified = cell_state(cell, cell_rows)
            cell["state"] = state
            cell["unverified"] = unverified

            for row in cell_rows:
                for ev in cell["evidence"]:
                    if ev["role"] != "tracker":
                        continue
                    if row["checked"] and ev["state"] == "open":
                        cell["disagreements"].append(
                            {"type": "checked_but_open", "ref": ev["ref"]})
                    if row["checked"] and ev["state"] == "not_planned":
                        cell["disagreements"].append(
                            {"type": "checked_but_not_planned", "ref": ev["ref"]})
                    if not row["checked"] and ev["state"] == "completed":
                        cell["disagreements"].append(
                            {"type": "unchecked_but_completed", "ref": ev["ref"]})
            # Linkage gaps are worth reporting but they are not the data
            # contradicting itself, so they do not raise the review flag.
            for ev in cell["evidence"]:
                if ev["role"] == "tracker" and ev["sources"] == ["row"]:
                    cell["linkage"].append(
                        {"type": "native_missing", "ref": ev["ref"]})
                if ev["role"] == "tracker" and ev["sources"] == ["native"] and cell_rows:
                    cell["linkage"].append(
                        {"type": "row_missing", "ref": ev["ref"]})
                if ev["role"] == "implementation" and ev["state"] == "closed":
                    cell["disagreements"].append(
                        {"type": "pr_unmerged", "ref": ev["ref"]})
            if unverified:
                cell["disagreements"].append(
                    {"type": "claimed_no_evidence", "ref": None})

            for field in ("disagreements", "linkage"):
                unique, keys = [], set()
                for item in cell[field]:
                    key = (item["type"], item["ref"])
                    if key in keys:
                        continue
                    keys.add(key)
                    item["message"] = DISAGREEMENTS[item["type"]]
                    unique.append(item)
                cell[field] = unique

        counts = {}
        for cell in cells.values():
            counts[cell["state"]] = counts.get(cell["state"], 0) + 1
        # Neither a declined issue nor an out-of-scope platform is work
        # outstanding, so neither belongs in the denominator.
        denominator = sum(v for k, v in counts.items()
                          if k not in ("not_planned", "not_applicable"))
        percent = round(100 * counts.get("shipped", 0) / denominator) if denominator else 0

        topics.append({
            "id": number,
            "url": issue["url"],
            "title": strip_prefixes(issue["title"]),
            "titleRaw": issue["title"],
            "state": issue["state"],
            "updatedAt": issue["updatedAt"],
            "labels": labels,
            "parent": (issue.get("parent") or {}).get("number"),
            "cells": cells,
            "other": [{"checked": r["checked"], "text": r["text"][:180],
                       "label": r["label"]} for r in rows if not r["platform"]],
            "blockedBy": [r["text"] for r in rows if r["blocked"]],
            "counts": counts,
            "percent": percent,
            "sources": sorted(set((["sub-issues"] if children else []) +
                                  (["body"] if rows else []) +
                                  ([] if (children or rows) else ["label"]))),
        })

        if children and "[PARENT]" not in issue["title"]:
            findings.append({
                "topic": number, "type": "unmarked_parent", "severity": "info",
                "message": "Has sub-issues but the title does not say [PARENT].",
            })
        if "[PARENT]" in issue["title"] and not (children or rows):
            findings.append({
                "topic": number, "type": "empty_parent", "severity": "warning",
                "message": "Titled [PARENT] but nothing is tracked under it.",
            })

    topics.sort(key=lambda t: (t["state"] != "OPEN", t["percent"],
                               -len(t["cells"]), t["id"]))
    used = {p for t in topics for p in t["cells"]}
    columns = [p for p in cfg["platforms"] if p["column"] and p["id"] in used]
    extra = [p for p in cfg["platforms"] if not p["column"] and p["id"] in used]

    return topics, findings, columns + extra, seen_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__),
                                                  "site", "data.json"))
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(__file__),
                                                    "refs-cache.json"))
    ap.add_argument("--history", default=None)
    ap.add_argument("--raw", default=None, help="Read issues from a file instead of the API")
    args = ap.parse_args()

    cfg = load_config()

    if args.raw:
        issues = json.load(open(args.raw))
        tok = None
    else:
        tok = token()
        issues = fetch_issues(tok)

    wanted = set()
    for issue in issues:
        rows, _ = parse_issue(issue["number"], issue["body"], cfg)
        for row in rows:
            for ref in row["refs"]:
                wanted.add((ref["repo"], ref["number"]))
        # The whole tree, not just direct children: build() merges descendants
        # upward, and a grandchild whose state was never looked up renders as
        # unknown rather than as whatever it actually is.
        for child in iter_descendants(issue):
            wanted.add((child["repository"]["nameWithOwner"], child["number"]))

    cache = {}
    if os.path.exists(args.cache):
        cache = json.load(open(args.cache))
    if tok:
        resolve_refs(sorted(wanted), tok, cache)
        with open(args.cache, "w") as fh:
            json.dump(cache, fh, indent=1, sort_keys=True)

    topics, findings, platforms, seen_rows = build(issues, cfg, cache)

    # Reconcile: every checkbox row in a tracking section must be accounted for.
    emitted = sum(len(t["other"]) for t in topics) + sum(
        len(c["notes"]) for t in topics for c in t["cells"].values())
    if emitted > seen_rows:
        sys.exit(f"Row reconciliation failed: emitted {emitted}, parsed {seen_rows}.")

    resolved = sum(1 for k in cache if cache[k].get("type"))
    data = {
        "schemaVersion": 1,
        "generatedAt": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generatedBy": {
            "runId": os.environ.get("GITHUB_RUN_ID"),
            "runUrl": (f'{os.environ.get("GITHUB_SERVER_URL","")}/'
                       f'{os.environ.get("GITHUB_REPOSITORY","")}/actions/runs/'
                       f'{os.environ.get("GITHUB_RUN_ID","")}')
                      if os.environ.get("GITHUB_RUN_ID") else None,
        },
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "platforms": [{"id": p["id"], "label": p["label"], "repos": p["repos"],
                       "column": p["column"]} for p in platforms],
        "topics": topics,
        "hygiene": findings,
        "stats": {
            "issuesScanned": len(issues),
            "topics": len(topics),
            "rows": seen_rows,
            "refsNeeded": len(wanted),
            "refsResolved": resolved,
        },
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(data, fh, separators=(",", ":"))

    if args.history:
        history = []
        if os.path.exists(args.history):
            history = json.load(open(args.history))
        today = data["generatedAt"][:10]
        history = [h for h in history if h["date"] != today]
        for topic in topics:
            if topic["state"] != "OPEN":
                continue
            history.append({"date": today, "topic": topic["id"],
                            "shipped": topic["counts"].get("shipped", 0),
                            "total": len(topic["cells"])})
        cutoff = (datetime.date.today()
                  - datetime.timedelta(days=HISTORY_DAYS)).isoformat()
        history = [h for h in history if h["date"] >= cutoff]
        with open(args.history, "w") as fh:
            json.dump(history, fh, separators=(",", ":"))

    print(json.dumps(data["stats"], indent=1))
    print(f"cells: {sum(len(t['cells']) for t in topics)}")
    print(f"hygiene findings: {len(findings)}")


if __name__ == "__main__":
    main()
