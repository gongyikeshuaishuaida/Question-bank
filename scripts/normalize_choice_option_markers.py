#!/usr/bin/env python3
"""Normalize ABCD option lines in question bodies to Markdown list items."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


OPTION_RE = re.compile(r"^(\s*)([ABCD])([\.．、])(\s|$)")


def read_frontmatter(text: str) -> dict[str, str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def question_body_bounds(text: str) -> tuple[int, int] | None:
    heading = re.search(r"^# .+$", text, flags=re.MULTILINE)
    if not heading:
        return None
    start = heading.end()
    answer = re.search(r"\n---\s*\n\s*## 答案\s*$", text[start:], flags=re.MULTILINE)
    if not answer:
        answer = re.search(r"^## 答案\s*$", text[start:], flags=re.MULTILINE)
    end = start + answer.start() if answer else len(text)
    return start, end


def normalize_body(body: str) -> str:
    lines = body.splitlines(keepends=True)
    in_code = False
    out: list[str] = []
    for line in lines:
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        out.append(OPTION_RE.sub(r"\1- \2\3\4", line, count=1))
    return "".join(out)


def iter_notes(root: Path, prefix: str | None) -> list[Path]:
    notes = [
        path
        for path in root.rglob("*.md")
        if path.parent.name[:2].isdigit()
        and not any(part in {".obsidian", ".codex-skills", "scripts"} for part in path.parts)
    ]
    if prefix:
        notes = [path for path in notes if path.name.startswith(prefix)]
    return sorted(notes)


def normalize(root: Path, prefix: str | None, dry_run: bool) -> int:
    changed = 0
    checked = 0
    for path in iter_notes(root, prefix):
        text = path.read_text(encoding="utf-8")
        if not read_frontmatter(text):
            continue
        bounds = question_body_bounds(text)
        if bounds is None:
            continue
        checked += 1
        start, end = bounds
        new_body = normalize_body(text[start:end])
        new_text = text[:start] + new_body + text[end:]
        if new_text != text:
            changed += 1
            if not dry_run:
                path.write_text(new_text, encoding="utf-8", newline="\n")
    mode = "would change" if dry_run else "changed"
    print(f"checked question notes: {checked}")
    print(f"{mode}: {changed}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--prefix", help="Only normalize note filenames with this prefix.")
    parser.add_argument("--write", action="store_true", help="Write changes. Omit for dry-run.")
    args = parser.parse_args()
    return normalize(args.root.resolve(), args.prefix, dry_run=not args.write)


if __name__ == "__main__":
    raise SystemExit(main())
