"""Markdown/YAML fragment parser.

A fragment is a fenced YAML block:

    ---
    id: dream-...
    type: SEED
    ---
    @HH:MM [TYPE] — body text

The parser tolerates:
* preamble before the first fragment;
* malformed / unterminated front matter (flagged fm_ok=False, not silently {});
* ``---`` appearing inside a body (only treated as a boundary when the following
  text parses as a valid front-matter candidate).
"""
from __future__ import annotations

import re

_FM_DELIM = re.compile(r"^\s*---\s*$", re.M)


def _looks_like_fm(candidate: str) -> bool:
    try:
        import yaml
        yaml.safe_load(candidate)
        return True
    except Exception:
        return False


def parse_document(text: str) -> list[dict]:
    """Return a list of blocks: {raw_fm, body, fm_ok, error}."""
    lines = text.split("\n")
    n = len(lines)
    blocks: list[dict] = []

    # skip preamble up to first delimiter
    i = 0
    while i < n and lines[i].strip() != "---":
        i += 1

    while i < n:
        if lines[i].strip() != "---":
            i += 1
            continue
        # front matter spans (i+1 .. j) where j is the closing '---'
        fm_start = i + 1
        j = fm_start
        while j < n and lines[j].strip() != "---":
            j += 1
        if j >= n:
            # unterminated front matter -> invalid block, body is remainder
            blocks.append({
                "raw_fm": "\n".join(lines[fm_start:]),
                "body": "",
                "fm_ok": False,
                "error": "unterminated front matter",
            })
            break
        raw_fm = "\n".join(lines[fm_start:j])
        body_start = j + 1
        # body runs until the next '---\n' that opens a NEW fragment
        k = body_start
        while k < n:
            if lines[k].strip() == "---":
                peek_end = k + 1
                while peek_end < n and lines[peek_end].strip() != "---":
                    peek_end += 1
                if peek_end < n and _looks_like_fm("\n".join(lines[k + 1:peek_end])):
                    break  # boundary
            k += 1
        body = "\n".join(lines[body_start:k]).strip()
        blocks.append({"raw_fm": raw_fm, "body": body, "fm_ok": True, "error": None})
        i = k  # resume at the boundary delimiter

    return blocks


def serialize_block(fm: dict, body: str) -> str:
    """Render a fragment block (front matter + body) for writing back to Markdown."""
    import yaml
    fm_yaml = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm_yaml}\n---\n\n{body}\n"
