from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ATTACHMENTS = ROOT / "attachments"
PAGES = ROOT / "_pdf_pages" / "current_batch_rebuild"
SCALE = 2.0


@dataclass(frozen=True)
class Paper:
    prefix: str
    count: int
    ranges: dict[tuple[int, int], list[tuple[int, float, float, float, float]]]
    choices: dict[int, str]


def safe_name(prefix: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", prefix)


def render(prefix: str) -> list[Path]:
    pdf = ROOT / "试卷" / f"{prefix}.pdf"
    out_dir = PAGES / safe_name(prefix)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    paths: list[Path] = []
    for idx, page in enumerate(doc, start=1):
        out = out_dir / f"p{idx:02d}.png"
        if not out.exists():
            pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
            pix.save(out)
        paths.append(out)
    return paths


def image_path(prefix: str, page_no: int) -> Path:
    return PAGES / safe_name(prefix) / f"p{page_no:02d}.png"


def crop(prefix: str, q: int, boxes: list[tuple[int, float, float, float, float]]) -> list[str]:
    names: list[str] = []
    simple = safe_name(prefix)
    for i, (page_no, lx, ty, rx, by) in enumerate(boxes, start=1):
        image = Image.open(image_path(prefix, page_no))
        w, h = image.size
        left, top, right, bottom = int(w * lx), int(h * ty), int(w * rx), int(h * by)
        out_name = f"{simple}_{q:02d}_题图{i}.png"
        out = ATTACHMENTS / out_name
        out.parent.mkdir(parents=True, exist_ok=True)
        image.crop((left, top, right, bottom)).save(out)
        names.append(out_name)
    return names


def boxes_for(paper: Paper, q: int) -> list[tuple[int, float, float, float, float]]:
    for (start, end), boxes in paper.ranges.items():
        if start <= q <= end:
            return boxes
    # Last-resort compact middle crop, should not normally be used.
    return [(1, 0.07, 0.25, 0.93, 0.93)]


def folder_for(q: int) -> str:
    if q <= 6:
        return "06信息系统"
    if q == 7:
        return "02算法"
    if q == 8:
        return "09队列"
    if q == 9:
        return "12树"
    if q == 10:
        return "03python基础"
    if q == 11:
        return "03python基础"
    if q == 12:
        return "03python基础"
    if q == 14:
        return "04数据处理"
    return "03python基础"


def question_type(q: int) -> str:
    return "选择题" if q <= 12 else "填空题"


def difficulty(q: int) -> str:
    if q <= 8:
        return "简单"
    if q <= 12:
        return "中等"
    return "困难"


def answer_for(paper: Paper, q: int) -> str:
    if q in paper.choices:
        return paper.choices[q]
    return "见参考答案"


def write_note(paper: Paper, q: int, image_names: list[str]) -> Path:
    folder = ROOT / folder_for(q)
    folder.mkdir(parents=True, exist_ok=True)
    note_id = f"{paper.prefix}-{q:02d}"
    pdf_name = f"{paper.prefix}.pdf"
    grade = paper.prefix.split("-")[-2]
    knowledge = folder.name
    path = folder / f"{note_id}.md"
    embeds = "\n\n".join(f"![[attachments/{name}]]" for name in image_names)
    text = f"""---
id: {note_id}
题型: {question_type(q)}
来源: "[[试卷/{pdf_name}|{pdf_name}]]"
试卷: {pdf_name}
年级: {grade}
题号: "{q:02d}"
难度: {difficulty(q)}
知识点:
  - {knowledge}
完成次数: 0
正确率:
状态: 未练习
错题原因:
创建日期: 2026-06-12
图片核验: 待核验
tags:
  - 状态/未练习
  - 知识点/{knowledge}
---
# 题目 {q:02d}

{embeds}

---

## 答案

**正确答案：** {answer_for(paper, q)}

---

## 解析

请对照原题截图和参考答案复核。

---

## 相关链接

- 原试卷：[[试卷/{pdf_name}|{pdf_name}]]
"""
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def build_pages(rows: list[tuple[Paper, Path, list[str]]]) -> None:
    image_lines = [
        "---",
        "title: 图片核验",
        "description: 每次试卷处理完成后，集中显示本批题目图片，便于检查裁切是否合适",
        "---",
        "",
        "# 图片核验",
        "",
        "本页只保留最近一次处理试卷产生或更新的题目图片。每次重新处理新的试卷时，先清空上一批图片，再写入本批图片。",
        "",
    ]
    note_lines = [
        "---",
        "title: 题目核验",
        "description: 每次处理新试卷后，集中列出本批新增或更新的题目 md",
        "---",
        "",
        "# 题目核验",
        "",
        "本页只保留最近一次处理试卷新增或更新的题目 md。每次重新处理新的试卷时，先清空上一批题目链接，再按试卷分组写入本批题目。",
        "",
    ]
    current = ""
    for paper, path, images in rows:
        if paper.prefix != current:
            current = paper.prefix
            image_lines.extend([f"## {paper.prefix}", ""])
            note_lines.extend([f"## {paper.prefix}", "", "| 题号 | 题型 | 知识点 | 题目 md |", "|---|---|---|---|"])
        rel = path.relative_to(ROOT).with_suffix("").as_posix()
        q = int(path.stem.rsplit("-", 1)[-1])
        image_lines.extend([f"### [[{rel}]]", ""])
        for image in images:
            image_lines.extend([f"![[attachments/{image}]]", ""])
        image_lines.extend(["图片核验：待核验", ""])
        note_lines.append(f"| {q:02d} | {question_type(q)} | {path.parent.name} | [[{rel}]] |")
    (ROOT / "图片核验.md").write_text("\n".join(image_lines) + "\n", encoding="utf-8", newline="\n")
    (ROOT / "题目核验.md").write_text("\n".join(note_lines) + "\n", encoding="utf-8", newline="\n")


COMMON_SCANNED = {
    (1, 4): [(1, 0.07, 0.38, 0.93, 0.93)],
    (5, 11): [(2, 0.07, 0.07, 0.93, 0.93)],
    (12, 13): [(3, 0.07, 0.07, 0.93, 0.93)],
    (14, 14): [(4, 0.07, 0.07, 0.93, 0.93)],
    (15, 15): [(5, 0.07, 0.07, 0.93, 0.93), (6, 0.07, 0.07, 0.93, 0.55)],
}


PAPERS = [
    Paper(
        "202604-温州-高三-二模",
        15,
        COMMON_SCANNED,
        {1: "C", 2: "A", 3: "C", 4: "A", 5: "B", 6: "D", 7: "A", 8: "B", 9: "C", 10: "C", 11: "B", 12: "B"},
    ),
    Paper(
        "202605-上虞-高三-月考",
        15,
        {
            (1, 3): [(1, 0.07, 0.28, 0.93, 0.93)],
            (4, 10): [(2, 0.07, 0.07, 0.93, 0.93)],
            (11, 13): [(3, 0.07, 0.07, 0.93, 0.93)],
            (14, 14): [(4, 0.07, 0.07, 0.93, 0.93), (5, 0.07, 0.07, 0.93, 0.93)],
            (15, 15): [(6, 0.07, 0.07, 0.93, 0.93), (7, 0.07, 0.07, 0.93, 0.55)],
        },
        {1: "B", 2: "D", 3: "D", 4: "A", 5: "A", 6: "C", 7: "D", 8: "B", 9: "A", 10: "C", 11: "D", 12: "C"},
    ),
    Paper(
        "202605-义乌柯桥-高三-月考",
        15,
        {
            (1, 5): [(1, 0.07, 0.35, 0.93, 0.93)],
            (6, 10): [(2, 0.07, 0.12, 0.93, 0.93)],
            (11, 13): [(3, 0.07, 0.07, 0.93, 0.93)],
            (14, 14): [(4, 0.07, 0.07, 0.93, 0.93)],
            (15, 15): [(5, 0.07, 0.07, 0.93, 0.93), (6, 0.07, 0.07, 0.93, 0.60)],
        },
        {},
    ),
    Paper(
        "202605-卓越联盟-高三-月考",
        15,
        {
            (1, 5): [(1, 0.07, 0.30, 0.93, 0.93)],
            (6, 12): [(2, 0.07, 0.08, 0.93, 0.93)],
            (13, 13): [(3, 0.07, 0.07, 0.93, 0.93)],
            (14, 14): [(4, 0.07, 0.07, 0.93, 0.93)],
            (15, 15): [(5, 0.07, 0.07, 0.93, 0.93), (6, 0.07, 0.07, 0.93, 0.60)],
        },
        {},
    ),
    Paper("202605-县域教研-高三-月考", 15, COMMON_SCANNED, {}),
    Paper(
        "202605-县域联盟-高二-学考",
        11,
        {
            (1, 4): [(1, 0.07, 0.30, 0.93, 0.93)],
            (5, 10): [(2, 0.07, 0.07, 0.93, 0.93)],
            (11, 11): [(3, 0.07, 0.07, 0.93, 0.93), (4, 0.07, 0.07, 0.93, 0.93), (5, 0.07, 0.07, 0.93, 0.60)],
        },
        {1: "B", 2: "A", 3: "D", 4: "C", 5: "D", 6: "B", 7: "B", 8: "C", 9: "A"},
    ),
    Paper(
        "202605-强基联盟-高三-月考",
        15,
        {
            (1, 6): [(1, 0.07, 0.31, 0.93, 0.93)],
            (7, 12): [(2, 0.07, 0.07, 0.93, 0.93)],
            (13, 13): [(3, 0.07, 0.07, 0.93, 0.93)],
            (14, 14): [(4, 0.07, 0.07, 0.93, 0.93)],
            (15, 15): [(5, 0.07, 0.07, 0.93, 0.93), (6, 0.07, 0.07, 0.93, 0.60)],
        },
        {},
    ),
    Paper(
        "202605-诸暨-高三-三模",
        15,
        {
            (1, 5): [(1, 0.07, 0.31, 0.93, 0.93)],
            (6, 11): [(2, 0.07, 0.12, 0.93, 0.93)],
            (12, 13): [(3, 0.07, 0.12, 0.93, 0.93)],
            (14, 14): [(4, 0.07, 0.12, 0.93, 0.93), (5, 0.07, 0.12, 0.93, 0.35)],
            (15, 15): [(5, 0.07, 0.32, 0.93, 0.93), (6, 0.07, 0.07, 0.93, 0.60)],
        },
        {1: "A", 2: "D", 3: "D", 4: "A", 5: "B", 6: "C", 7: "A", 8: "B", 9: "C", 10: "B", 11: "B", 12: "D"},
    ),
]


def main() -> None:
    rows: list[tuple[Paper, Path, list[str]]] = []
    for paper in PAPERS:
        render(paper.prefix)
        for q in range(1, paper.count + 1):
            images = crop(paper.prefix, q, boxes_for(paper, q))
            note = write_note(paper, q, images)
            rows.append((paper, note, images))
    build_pages(rows)
    print(f"created {len(rows)} notes")
    print(f"created {sum(len(images) for _, _, images in rows)} image references")


if __name__ == "__main__":
    main()
