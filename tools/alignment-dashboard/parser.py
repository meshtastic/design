"""Parse the tracking lists out of meshtastic/design issue bodies.

Pure functions, no network. The design repo tracks cross-platform work three
different ways and none of them is authoritative on its own, so this module
extracts what it can and records what it could not, rather than guessing.
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config(path=None):
    with open(path or os.path.join(HERE, "platforms.json")) as fh:
        return json.load(fh)


HEADING = re.compile(r"^(#{2,6})\s*(.+?)\s*$", re.M)
ROW = re.compile(r"^([ \t]*)[-*+]\s*\[([ xX])\]\s*(.*)$")
CONTEXT = re.compile(r"^\s*\*{0,2}([A-Za-z][^:\n]{0,38}?)\*{0,2}:\s*$")
VERB = re.compile(
    r"^(create|define|resolve|document|add|hardware|operator|on-device)\b", re.I
)
SEPARATOR = re.compile(r",|\s[—–-]\s|:")

NOT_FILED = re.compile(
    r"not (yet )?filed|no tracker opened|not started|neither started|no tracker", re.I
)
BLOCKED = re.compile(r"blocked (on|by)\b", re.I)
SHIPPED_IN = re.compile(r"shipped in|merged in|landed in", re.I)

# Reference forms, most specific first. A /blob/ URL is a code permalink whose
# #L33 fragment would otherwise be read as an issue number.
PERMALINK = re.compile(r"https?://github\.com/[\w.-]+/[\w.-]+/blob/\S+")
CODE_SPAN = re.compile(r"`[^`]*`")
REF_MD = re.compile(
    r"\[[^\]]*\]\((https?://github\.com/([\w.-]+)/([\w.-]+)/(issues|pull)/(\d+))[^)]*\)"
)
REF_URL = re.compile(r"https?://github\.com/([\w.-]+)/([\w.-]+)/(issues|pull)/(\d+)")
REF_OWNER_REPO = re.compile(r"(?<![\w/\[])([\w.-]+/[\w.-]+)#(\d+)")
REF_REPO = re.compile(r"(?<![\w/#\[.-])([A-Za-z][\w.-]*)#(\d+)")
REF_BARE = re.compile(r"(?<![\w/#.-])#(\d+)")
SHA = re.compile(r"(?<![\w#])`?([0-9a-f]{7,40})`?(?![\w])")


def normalize_body(body):
    """Strip anything a reference regex must never see."""
    text = (body or "").replace("\r\n", "\n")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text


def normalize_heading(title):
    return title.strip().lower().rstrip(":.").strip()


def extract_refs(text, shorthand):
    """Left to right, carrying the repo forward so a bare #N inherits it.

    Returns a list of {repo, number, kind, inherited}. `kind` is None when the
    form does not say whether the target is an issue or a pull request; the
    caller resolves those against the API rather than guessing.
    """
    cleaned = PERMALINK.sub(" ", text)
    cleaned = CODE_SPAN.sub(" ", cleaned)

    spans = []

    def claim(match, repo, number, kind):
        if any(s <= match.start() < e for s, e, _, _, _ in spans):
            return
        spans.append((match.start(), match.end(), repo, number, kind))

    for m in REF_MD.finditer(cleaned):
        claim(m, f"{m.group(2)}/{m.group(3)}", m.group(5),
              "PR" if m.group(4) == "pull" else "ISSUE")
    for m in REF_URL.finditer(cleaned):
        claim(m, f"{m.group(1)}/{m.group(2)}", m.group(4),
              "PR" if m.group(3) == "pull" else "ISSUE")
    for m in REF_OWNER_REPO.finditer(cleaned):
        claim(m, m.group(1), m.group(2), None)
    for m in REF_REPO.finditer(cleaned):
        name = m.group(1)
        if name.lower() in ("l", "http", "https"):
            continue
        claim(m, f"meshtastic/{shorthand.get(name, name)}", m.group(2), None)
    for m in REF_BARE.finditer(cleaned):
        claim(m, None, m.group(1), None)

    refs, current = [], None
    for _, _, repo, number, kind in sorted(spans):
        inherited = repo is None
        if inherited:
            repo = current or "meshtastic/design"
        else:
            current = repo
        refs.append({"repo": repo, "number": int(number), "kind": kind,
                     "inherited": inherited})
    return refs


def leading_alias(text, cfg):
    """The longest configured alias the row starts with, or None.

    Checked before the separator split so an alias that contains a comma, such
    as "Apple (iOS, iPadOS, macOS)", is not cut in half and turned into a label
    of "Apple (iOS" carrying a junk aspect.
    """
    low = re.sub(r"\*\*", "", text).strip().lower()
    best = None
    for alias in cfg["aliases"]:
        if not low.startswith(alias):
            continue
        tail = low[len(alias):]
        if tail and (tail[0].isalnum() or tail[0] == "-"):
            continue
        if best is None or len(alias) > len(best):
            best = alias
    return best


def normalize_platform(label, cfg):
    """Map a free-text row label to a platform id, plus any trailing aspect."""
    key = re.sub(r"\*\*", "", label or "").strip().lower()
    key = key.rstrip(".:—–-").strip()
    if not key:
        return None, None
    aliases = cfg["aliases"]
    if key in aliases:
        return aliases[key], None
    for alias in sorted(aliases, key=len, reverse=True):
        if key.startswith(alias + " ") or key.startswith(alias + ","):
            aspect = key[len(alias):].strip(" ,—–-")
            return aliases[alias], aspect or None
    return None, None


def parse_issue(number, body, cfg):
    """Return (rows, findings) for one issue body.

    Every checkbox row inside a tracking section is emitted, including ones
    whose platform could not be determined. Nothing is silently dropped.
    """
    text = normalize_body(body)
    lines = text.split("\n")
    headings = list(HEADING.finditer(text))
    shorthand = cfg["repo_shorthand"]
    repo_to_platform = {
        repo: p["id"] for p in cfg["platforms"] for repo in p["repos"]
    }
    platform_repos = {p["id"]: p["repos"][0] for p in cfg["platforms"]}
    tracking = set(cfg["tracking_headings"])
    ignored = set(cfg["ignored_headings"])

    # Map character offsets to 1-based line numbers for provenance.
    offsets, pos = [], 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    def line_of(offset):
        lo, hi = 0, len(offsets) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if offsets[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    rows, findings = [], []
    for index, match in enumerate(headings):
        title = match.group(2).strip()
        key = normalize_heading(title)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[match.end():end]

        if key in ignored:
            continue
        if key not in tracking:
            if not re.search(r"track|client|platform|status", key):
                continue
            if not any(ROW.match(ln) for ln in section.split("\n")):
                continue
            findings.append({
                "topic": number, "type": "heading_unrecognized", "severity": "info",
                "message": f"Heading “{title}” holds checkboxes but is not a "
                           "known tracking heading. It was parsed anyway.",
            })

        context_platform = None
        section_start = match.end()
        for raw in section.split("\n"):
            offset = text.find(raw, section_start) if raw else section_start
            if raw:
                section_start = offset + len(raw)

            row = ROW.match(raw)
            if not row:
                ctx = CONTEXT.match(raw)
                if ctx:
                    platform, _ = normalize_platform(ctx.group(1), cfg)
                    if platform:
                        context_platform = platform
                continue

            checked = row.group(2).lower() == "x"
            content = row.group(3).strip()
            refs = extract_refs(content, shorthand)
            label = re.sub(r"\*\*", "", SEPARATOR.split(content, maxsplit=1)[0]).strip()

            platform, aspect, how = None, None, None
            if context_platform:
                platform, how = context_platform, "context"

            alias = leading_alias(content, cfg)
            if platform is None and alias:
                platform, how = cfg["aliases"][alias], "label"
                stripped = re.sub(r"\*\*", "", content).strip()
                tail = SEPARATOR.split(stripped[len(alias):], maxsplit=1)[0].strip()
                if tail and len(tail) <= 40 and not re.search(r"#\d|https?://", tail):
                    aspect = tail
                label = stripped[:len(alias)]

            if platform is None and label:
                bare = re.sub(r"\[|\]\([^)]*\)", "", label).strip()
                if len(bare) <= 44 and not re.search(r"#\d|https?://", label):
                    if VERB.match(bare):
                        how = "meta"
                    else:
                        platform, aspect = normalize_platform(bare, cfg)
                        how = "label" if platform else None
            if platform is None and refs and content.lstrip().startswith(("[", "http")):
                platform = repo_to_platform.get(refs[0]["repo"])
                how = "ref" if platform else None

            # A bare #N with no qualified reference before it in the row
            # defaults to this repo, which is wrong when the row is about a
            # client: "Meshtastic Apple — ... the merged #2033 notice" means
            # Meshtastic-Apple#2033. Re-point those once the platform is known.
            if platform:
                home = platform_repos.get(platform)
                if home:
                    for ref in refs:
                        if ref["inherited"] and ref["repo"] == "meshtastic/design":
                            ref["repo"] = home

            if platform is None and how != "meta":
                findings.append({
                    "topic": number, "type": "platform_unmapped", "severity": "info",
                    "message": f"Row label “{label[:60]}” did not map to a "
                               "platform.", "rowText": content[:200],
                })

            rows.append({
                "topic": number,
                "checked": checked,
                "text": content,
                "label": label[:60],
                "platform": platform,
                "aspect": aspect,
                "how": how,
                "refs": refs,
                "notFiled": bool(NOT_FILED.search(content)),
                "blocked": bool(BLOCKED.search(content)),
                "shippedIn": bool(SHIPPED_IN.search(content)),
                "heading": title,
                "line": line_of(offset),
            })

    return rows, findings


def count_checkbox_rows(body):
    """Every checkbox row in the body, tracking or not. Used to reconcile."""
    return sum(1 for ln in normalize_body(body).split("\n") if ROW.match(ln))
