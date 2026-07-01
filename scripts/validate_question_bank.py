#!/usr/bin/env python3
"""Validate local Obsidian question-bank notes."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_FIELDS = [
    "id",
    "题型",
    "来源",
    "试卷",
    "题号",
    "难度",
    "知识点",
    "完成次数",
    "正确率",
    "状态",
    "错题原因",
    "创建日期",
    "图片核验",
    "tags",
]

STALE_TERMS = ["正确次数", "下次复习", "上次练习", "待补充"]


def split_markdown_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def read_frontmatter(text: str) -> dict[str, str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    frontmatter = text[4:end].splitlines()
    data: dict[str, str] = {}
    for line in frontmatter:
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def section_text(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^## |\n---\n", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def question_body(text: str) -> str:
    match = re.search(r"^# 题目 \d{2}\s*$", text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    answer_match = re.search(r"\n---\n\n## 答案\s*$", text[start:], flags=re.MULTILINE)
    end = start + answer_match.start() if answer_match else len(text)
    return text[start:end].strip()


def strip_code_blocks(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def bare_choice_option_lines(body: str) -> list[int]:
    body = strip_code_blocks(body)
    lines: list[int] = []
    for lineno, line in enumerate(body.splitlines(), start=1):
        if re.match(r"^\s*[ABCD][\.．、](?:\s|$)", line):
            lines.append(lineno)
    return lines


def choice_question_numbers(body: str) -> list[int]:
    markers = [
        (int(match.group(1)), match.start())
        for match in re.finditer(r"(?m)^\s*(\d{1,2})[\.．、]\s+", body)
    ]
    numbers: list[int] = []
    for idx, (number, start) in enumerate(markers):
        end = markers[idx + 1][1] if idx + 1 < len(markers) else len(body)
        segment = body[start:end]
        options = set(re.findall(r"(?m)^\s*(?:- )?([ABCD])[\.．、]", segment))
        if len(options) >= 4 or ("（   ）" in segment and "![[" in segment):
            numbers.append(number)
    return numbers


def iter_notes(root: Path, prefix: str | None) -> list[Path]:
    files = sorted(
        path
        for path in root.rglob("*.md")
        if path.parent.name[:2].isdigit()
    )
    if prefix:
        files = [path for path in files if path.name.startswith(prefix)]
    return [
        path
        for path in files
        if not any(part in {".obsidian", ".codex-skills", "scripts"} for part in path.parts)
    ]


def validate_note(root: Path, path: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(root)
    text = path.read_text(encoding="utf-8")
    meta = read_frontmatter(text)

    if not meta:
        return [f"{rel}: missing frontmatter"]

    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"{rel}: missing field {field}")

    note_id = meta.get("id")
    if note_id and note_id != path.stem:
        errors.append(f"{rel}: id does not match filename ({note_id})")

    for term in STALE_TERMS:
        if term in text:
            errors.append(f"{rel}: contains stale/placeholder term {term}")

    answer = section_text(text, "答案")
    analysis = section_text(text, "解析")
    if not answer:
        errors.append(f"{rel}: empty or missing ## 答案")
    if not analysis:
        errors.append(f"{rel}: empty or missing ## 解析")

    body = question_body(text)
    bare_option_lines = bare_choice_option_lines(body)
    if bare_option_lines:
        preview = ", ".join(str(line) for line in bare_option_lines[:8])
        if len(bare_option_lines) > 8:
            preview += ", ..."
        errors.append(f"{rel}: ABCD options must use '- A.' list format, bare option line(s) {preview}")

    if meta.get("题型") == "选择题" and re.search(r"阅读.{0,20}材料", body):
        try:
            note_q = int(meta.get("题号", "0"))
        except ValueError:
            note_q = 0
        question_numbers = choice_question_numbers(body)
        if note_q and note_q not in question_numbers:
            errors.append(f"{rel}: material choice note missing current question {note_q:02d}")
        extra_questions = [q for q in question_numbers if q != note_q]
        if extra_questions:
            errors.append(
                f"{rel}: material choice note includes other question(s) "
                + ", ".join(f"{q:02d}" for q in extra_questions)
            )

    embeds = re.findall(r"!\[\[attachments/([^\]]+)\]\]", text)
    image_status = meta.get("图片核验", "")
    if embeds and image_status == "无图片":
        errors.append(f"{rel}: has image embeds but 图片核验 is 无图片")
    if not embeds and image_status != "无图片":
        errors.append(f"{rel}: no image embeds but 图片核验 is {image_status}")
    for embed in embeds:
        attachment = root / "attachments" / embed
        if not attachment.exists():
            errors.append(f"{rel}: missing attachment {attachment.relative_to(root)}")

    return errors


def validate_review_table(root: Path) -> list[str]:
    path = root / "题目核验.md"
    if not path.exists():
        return []

    errors: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = split_markdown_table_row(stripped)
        if len(cells) != 4:
            errors.append(f"题目核验.md:{lineno}: table row has {len(cells)} columns, expected 4")
        if re.search(r"\[\[[^\]]+\|[^\]]+\]\]", stripped):
            errors.append(f"题目核验.md:{lineno}: table link must not use wiki alias syntax with |")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--prefix", help="Only validate note filenames with this prefix.")
    args = parser.parse_args()

    root = args.root.resolve()
    errors: list[str] = []
    notes = iter_notes(root, args.prefix)
    for path in notes:
        errors.extend(validate_note(root, path))
    errors.extend(validate_review_table(root))

    for error in errors:
        print(f"ERROR: {error}")
    print(f"checked {len(notes)} note(s), errors {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
