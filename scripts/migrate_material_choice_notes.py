#!/usr/bin/env python3
"""Migrate material choice notes to one question per note."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


RANGE_RE = re.compile(
    r"阅读[^\n]{0,40}材料[^\n]*?(?:回答|完成)第\s*(\d{1,2})\s*"
    r"(?:至第?|[-~－—–])\s*(\d{1,2})\s*题[。:：]?"
)
QUESTION_RE = re.compile(r"(?m)^\s*(\d{1,2})[\.．、]\s+")
OPTION_RE = re.compile(r"(?m)^\s*(?:- )?([ABCD])[\.．、]")


@dataclass
class Candidate:
    path: Path
    note_id: str
    qno: int
    start_q: int
    end_q: int
    body_start: int
    body_end: int
    material: str
    blocks: dict[int, str]

    @property
    def group_key(self) -> tuple[str, int, int]:
        return (self.note_id.rsplit("-", 1)[0], self.start_q, self.end_q)


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


def note_body_bounds(text: str) -> tuple[int, int] | None:
    match = re.search(r"^# 题目 \d{2}\s*$", text, flags=re.MULTILINE)
    if not match:
        return None
    body_start = match.end()
    answer_match = re.search(r"\n---\s*\n\s*## 答案\s*$", text[body_start:], flags=re.MULTILINE)
    body_end = body_start + answer_match.start() if answer_match else len(text)
    return body_start, body_end


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


def strip_material_prompt(material: str) -> str:
    return RANGE_RE.sub("", material, count=1).strip()


def question_blocks(body: str, start_q: int, end_q: int) -> tuple[str, dict[int, str]]:
    markers = [
        (int(match.group(1)), match.start())
        for match in QUESTION_RE.finditer(body)
        if start_q <= int(match.group(1)) <= end_q
    ]
    blocks: dict[int, str] = {}
    first_block_start: int | None = None
    for idx, (number, start) in enumerate(markers):
        end = markers[idx + 1][1] if idx + 1 < len(markers) else len(body)
        block = body[start:end].strip()
        options = set(OPTION_RE.findall(block))
        if len(options) >= 4 or ("（   ）" in block and "![[" in block):
            blocks[number] = block
            if first_block_start is None or start < first_block_start:
                first_block_start = start
    material_end = first_block_start if first_block_start is not None else len(body)
    material = strip_material_prompt(body[:material_end])
    return material, blocks


def candidate_for(path: Path) -> Candidate | None:
    text = path.read_text(encoding="utf-8")
    meta = read_frontmatter(text)
    if meta.get("题型") != "选择题":
        return None
    bounds = note_body_bounds(text)
    if bounds is None:
        return None
    body_start, body_end = bounds
    body = text[body_start:body_end].strip()
    range_match = RANGE_RE.search(body)
    if not range_match:
        return None
    start_q, end_q = sorted(map(int, range_match.groups()))
    try:
        qno = int(meta.get("题号", "0"))
    except ValueError:
        return None
    if not start_q <= qno <= end_q:
        return None
    note_id = meta.get("id", path.stem)
    material, blocks = question_blocks(body, start_q, end_q)
    return Candidate(path, note_id, qno, start_q, end_q, body_start, body_end, material, blocks)


def build_group_data(candidates: list[Candidate]) -> dict[tuple[str, int, int], tuple[str, dict[int, str]]]:
    grouped: dict[tuple[str, int, int], list[Candidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.group_key, []).append(candidate)

    result: dict[tuple[str, int, int], tuple[str, dict[int, str]]] = {}
    for key, items in grouped.items():
        material = max((item.material for item in items), key=len, default="")
        blocks: dict[int, str] = {}
        for item in items:
            for qno, block in item.blocks.items():
                if qno not in blocks or len(block) > len(blocks[qno]):
                    blocks[qno] = block
        result[key] = (material, blocks)
    return result


def migrated_body(candidate: Candidate, material: str, block: str) -> str:
    parts = [f"阅读下列材料，回答第 {candidate.qno:02d} 题。"]
    if material:
        parts.append(material)
    parts.append(block.strip())
    return "\n\n" + "\n\n".join(parts).strip() + "\n\n"


def sync_image_status(text: str) -> str:
    body_has_image = "![[" in text
    if body_has_image:
        return text
    return re.sub(r"(?m)^图片核验:\s*(?!无图片$).*$", "图片核验: 无图片", text, count=1)


def migrate(root: Path, prefix: str | None, dry_run: bool) -> int:
    candidates = [candidate for path in iter_notes(root, prefix) if (candidate := candidate_for(path))]
    group_data = build_group_data(candidates)
    changed = 0
    skipped: list[str] = []

    for candidate in candidates:
        material, blocks = group_data[candidate.group_key]
        block = candidate.blocks.get(candidate.qno) or blocks.get(candidate.qno)
        if not block:
            skipped.append(str(candidate.path.relative_to(root)))
            continue
        text = candidate.path.read_text(encoding="utf-8")
        new_text = text[: candidate.body_start] + migrated_body(candidate, material, block) + text[candidate.body_end :]
        new_text = sync_image_status(new_text)
        if new_text != text:
            changed += 1
            if not dry_run:
                candidate.path.write_text(new_text, encoding="utf-8", newline="\n")

    mode = "would change" if dry_run else "changed"
    print(f"material choice candidates: {len(candidates)}")
    print(f"{mode}: {changed}")
    print(f"skipped: {len(skipped)}")
    for item in skipped[:20]:
        print(f"SKIP: {item}")
    if len(skipped) > 20:
        print(f"SKIP: ... {len(skipped) - 20} more")
    return 1 if skipped else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--prefix", help="Only migrate note filenames with this prefix.")
    parser.add_argument("--write", action="store_true", help="Write changes. Omit for dry-run.")
    args = parser.parse_args()
    return migrate(args.root.resolve(), args.prefix, dry_run=not args.write)


if __name__ == "__main__":
    raise SystemExit(main())
