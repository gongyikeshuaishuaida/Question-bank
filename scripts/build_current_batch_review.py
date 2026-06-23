from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PREFIXES = [
    "202604-温州-高三-二模",
    "202605-上虞-高三-月考",
    "202605-义乌柯桥-高三-月考",
    "202605-卓越联盟-高三-月考",
    "202605-县域教研-高三-月考",
    "202605-县域联盟-高二-学考",
    "202605-强基联盟-高三-月考",
    "202605-诸暨-高三-三模",
]


def field(text: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}:\s*\"?([^\"\n\r]*)", text, flags=re.M)
    return match.group(1).strip() if match else ""


def knowledge(text: str) -> str:
    match = re.search(r"^知识点:\s*\n\s*-\s*([^\n\r]+)", text, flags=re.M)
    return match.group(1).strip() if match else ""


def note_link(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("").as_posix()
    return f"[[{rel}]]"


def current_batch_notes(prefix: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob(f"{prefix}-*.md")
        if not any(part in {".obsidian", ".codex-skills", "scripts"} for part in path.parts)
    )


def main() -> None:
    lines = [
        "---",
        "title: 题目核验",
        "description: 每次处理新试卷后，集中列出本批新增或更新的题目 md",
        "---",
        "",
        "# 题目核验",
        "",
        "本页只保留最近一次处理试卷新增或更新的题目 md。每次重新处理新的试卷时，先清空上一批题目链接，再按试卷分组写入本批题目。",
        "",
        "当前批次：" + "；".join(PREFIXES),
        "",
    ]

    for prefix in PREFIXES:
        notes = current_batch_notes(prefix)
        lines.extend(
            [
                f"## {prefix}",
                "",
                "| 题号 | 题型 | 知识点 | 题目 md |",
                "|---|---|---|---|",
            ]
        )
        for path in notes:
            text = path.read_text(encoding="utf-8")
            lines.append(
                f"| {field(text, '题号')} | {field(text, '题型')} | {knowledge(text)} | {note_link(path)} |"
            )
        lines.append("")

    (ROOT / "题目核验.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {ROOT / '题目核验.md'}")


if __name__ == "__main__":
    main()
