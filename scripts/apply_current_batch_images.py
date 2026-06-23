from __future__ import annotations

import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ATTACHMENTS = ROOT / "attachments"

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


def safe_name(prefix: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", prefix)


def note_paths(prefix: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob(f"{prefix}-*.md")
        if not any(part in {".obsidian", ".codex-skills", "scripts"} for part in path.parts)
    )


def qno(path: Path) -> str:
    return path.stem.rsplit("-", 1)[-1]


def image_names_for(prefix: str, q: str) -> list[str]:
    simple = safe_name(prefix)
    return sorted(path.name for path in ATTACHMENTS.glob(f"{simple}_{q}_原题*.png"))


def split_frontmatter(text: str) -> tuple[str, str]:
    end = text.find("\n---", 4) if text.startswith("---\n") else -1
    if end == -1:
        return "", text
    return text[: end + 4], text[end + 4 :].lstrip()


def set_field(frontmatter: str, key: str, value: str) -> str:
    return re.sub(rf"^{re.escape(key)}:.*$", f"{key}: {value}", frontmatter, flags=re.M)


def get_section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", body, flags=re.M)
    if not match:
        return ""
    start = match.start()
    rest = body[match.end() :]
    next_match = re.search(r"^## |\n---\n", rest, flags=re.M)
    end = match.end() + next_match.start() if next_match else len(body)
    return body[start:end].strip()


def rewrite_note(path: Path, images: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    if not frontmatter:
        return
    status = "待核验" if images else "无图片"
    frontmatter = set_field(frontmatter, "图片核验", status)
    embeds = "\n".join(f"![[attachments/{name}]]" for name in images)
    answer = get_section(body, "答案") or "## 答案\n\n**正确答案：** 见原答案复核"
    analysis = get_section(body, "解析") or "## 解析\n\n对照原题截图和参考答案复核。"
    links = get_section(body, "相关链接")
    parts = [
        frontmatter,
        f"# 题目 {qno(path)}",
        "",
    ]
    if embeds:
        parts.extend(
            [
                "原题局部截图如下。",
                "",
                embeds,
                "",
            ]
        )
    else:
        parts.extend(["未能自动裁出原题局部截图，请人工复核。", ""])
    if "OCR 识别" in answer or "见原答案复核" in answer:
        answer = "## 答案\n\n**正确答案：** 见参考答案复核"
    if "OCR 识别" in analysis or "依据原卷与参考答案整理" in analysis:
        analysis = "## 解析\n\n请对照原题局部截图和参考答案复核。"
    parts.extend(["---", "", answer, "", "---", "", analysis])
    if links:
        parts.extend(["", "---", "", links])
    path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8", newline="\n")


def crop_zhujii() -> None:
    prefix = "202605-诸暨-高三-三模"
    simple = safe_name(prefix)
    base = ROOT / "_pdf_pages" / "current_batch_rework" / simple
    # Coordinates are on 2x rendered page images. Each crop is a question-local area, not a full page.
    specs: dict[str, list[tuple[int, int, int, int, int]]] = {
        "01": [(1, 230, 880, 1440, 1105)],
        "02": [(1, 230, 1100, 1440, 1335)],
        "03": [(1, 230, 1330, 1440, 1605)],
        "04": [(1, 230, 1600, 1440, 1875)],
        "05": [(1, 230, 1870, 1440, 2135)],
        "06": [(2, 230, 330, 1440, 555)],
        "07": [(2, 230, 555, 1440, 795)],
        "08": [(2, 230, 790, 1440, 935)],
        "09": [(2, 230, 930, 1440, 1065)],
        "10": [(2, 230, 1060, 1440, 1585)],
        "11": [(2, 230, 1580, 1440, 2170)],
        "12": [(3, 230, 315, 1440, 1115)],
        "13": [(3, 230, 1110, 1440, 2160)],
        "14": [(4, 230, 315, 1440, 2160), (5, 230, 315, 1440, 760)],
        "15": [(5, 230, 755, 1440, 2160)],
    }
    for q, boxes in specs.items():
        for idx, (page, left, top, right, bottom) in enumerate(boxes, start=1):
            image = Image.open(base / f"p{page:02d}.png")
            suffix = "" if idx == 1 else f"_p{page}"
            out = ATTACHMENTS / f"{simple}_{q}_原题{suffix}.png"
            image.crop((left, top, right, bottom)).save(out)


def fallback_crop_missing() -> None:
    # Coarse question-local fallback for notes that did not get a detected crop.
    # This deliberately excludes page margins/header/footer, and is only for review.
    page_band = {
        1: (1, 520, 910),
        2: (1, 880, 1190),
        3: (1, 1160, 1470),
        4: (1, 1440, 1760),
        5: (1, 1730, 2140),
        6: (2, 300, 540),
        7: (2, 500, 760),
        8: (2, 730, 950),
        9: (2, 920, 1100),
        10: (2, 1060, 1560),
        11: (2, 1520, 2160),
        12: (3, 300, 920),
        13: (3, 860, 2160),
        14: (4, 300, 2160),
        15: (5, 300, 2160),
    }
    for prefix in PREFIXES:
        simple = safe_name(prefix)
        base = ROOT / "_pdf_pages" / "current_batch_rework" / simple
        pages = sorted(base.glob("p*.png"))
        if not pages:
            continue
        for note in note_paths(prefix):
            q = qno(note)
            if image_names_for(prefix, q):
                continue
            page_no, top, bottom = page_band.get(int(q), (1, 300, 2160))
            page_no = min(page_no, len(pages))
            image = Image.open(base / f"p{page_no:02d}.png")
            width, height = image.size
            left = int(width * 0.13)
            right = int(width * 0.88)
            top = max(0, min(top, height - 120))
            bottom = min(height, max(bottom, top + 120))
            out = ATTACHMENTS / f"{simple}_{q}_原题_兜底.png"
            image.crop((left, top, right, bottom)).save(out)


def build_image_review(rows: list[tuple[str, Path, list[str]]]) -> None:
    lines = [
        "---",
        "title: 图片核验",
        "description: 每次试卷处理完成后，集中显示本批题目图片，便于检查裁切是否合适",
        "---",
        "",
        "# 图片核验",
        "",
        "本页只保留最近一次处理试卷产生或更新的题目图片。每次重新处理新的试卷时，先清空上一批图片，再写入本批图片。",
        "",
        "当前批次：" + "；".join(PREFIXES),
        "",
    ]
    current = ""
    for prefix, note, images in rows:
        if prefix != current:
            current = prefix
            lines.extend([f"## {prefix}", ""])
        link = note.relative_to(ROOT).with_suffix("").as_posix()
        lines.extend([f"### [[{link}]]", ""])
        for image in images:
            lines.extend([f"![[attachments/{image}]]", ""])
        lines.extend([f"图片核验：{'待核验' if images else '无图片'}", ""])
    (ROOT / "图片核验.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    crop_zhujii()
    fallback_crop_missing()
    rows: list[tuple[str, Path, list[str]]] = []
    for prefix in PREFIXES:
        for note in note_paths(prefix):
            images = image_names_for(prefix, qno(note))
            rewrite_note(note, images)
            rows.append((prefix, note, images))
    build_image_review(rows)
    image_count = sum(len(images) for _prefix, _note, images in rows)
    print(f"updated {len(rows)} notes, referenced {image_count} images")


if __name__ == "__main__":
    main()
