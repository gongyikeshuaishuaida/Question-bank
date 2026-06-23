from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ATTACHMENTS = ROOT / "attachments"
RENDERED = ROOT / "_pdf_pages" / "current_batch_rework"
SCALE = 2.0

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


@dataclass(frozen=True)
class QStart:
    qno: int
    page: int
    y: float
    source: str


def safe_name(prefix: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", prefix)


def note_paths(prefix: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob(f"{prefix}-*.md")
        if not any(part in {".obsidian", ".codex-skills", "scripts"} for part in path.parts)
    )


def read_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---", 4)
    if end == -1:
        return "", text
    return text[: end + 4], text[end + 4 :].lstrip()


def set_frontmatter_value(frontmatter: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    replacement = f"{key}: {value}"
    if pattern.search(frontmatter):
        return pattern.sub(replacement, frontmatter)
    return frontmatter[:-4] + replacement + "\n---"


def section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, flags=re.M)
    if not match:
        return ""
    start = match.start()
    next_match = re.search(r"^## ", text[match.end() :], flags=re.M)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def answer_and_analysis(body: str) -> tuple[str, str]:
    answer = section(body, "答案") or "## 答案\n\n**正确答案：** 见原答案复核"
    analysis = section(body, "解析") or "## 解析\n\n请对照原题截图和参考答案复核。"
    links = section(body, "相关链接")
    tail = f"\n\n---\n\n{links}" if links else ""
    return answer, analysis + tail


def question_number(path: Path) -> int:
    return int(path.stem.rsplit("-", 1)[-1])


def render_pages(prefix: str) -> list[Path]:
    pdf = ROOT / "试卷" / f"{prefix}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    out_dir = RENDERED / safe_name(prefix)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    doc = fitz.open(pdf)
    matrix = fitz.Matrix(SCALE, SCALE)
    for idx, page in enumerate(doc, start=1):
        out = out_dir / f"p{idx:02d}.png"
        if not out.exists():
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(out)
        rendered.append(out)
    return rendered


QUESTION_RE = re.compile(r"^\s*([1-9]|1[0-5])\s*[\.。．、]")
BAD_START_TERMS = ("答题前", "准考证", "注意事项", "本试题卷", "考生")


def text_starts_from_pdf(prefix: str) -> list[QStart]:
    pdf = ROOT / "试卷" / f"{prefix}.pdf"
    starts: list[QStart] = []
    doc = fitz.open(pdf)
    for page_index, page in enumerate(doc):
        for block in page.get_text("blocks"):
            x0, y0, _x1, _y1, text, *_ = block
            for raw in text.splitlines():
                line = raw.strip()
                if not line or any(term in line for term in BAD_START_TERMS):
                    continue
                match = QUESTION_RE.match(line)
                if match:
                    qno = int(match.group(1))
                    if y0 * SCALE > 160:
                        starts.append(QStart(qno=qno, page=page_index, y=y0 * SCALE, source="text"))
                    break
    return starts


def ocr_starts_from_images(images: list[Path]) -> list[QStart]:
    try:
        import easyocr  # type: ignore
        import numpy as np
    except Exception:
        return []

    reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    starts: list[QStart] = []
    for page_index, image_path in enumerate(images):
        image_array = np.array(Image.open(image_path).convert("RGB"))
        result = reader.readtext(image_array, detail=1, paragraph=False)
        for box, text, _conf in result:
            line = str(text).strip()
            if not line or any(term in line for term in BAD_START_TERMS):
                continue
            match = QUESTION_RE.match(line)
            if not match:
                continue
            y = min(point[1] for point in box)
            if y > 160:
                starts.append(QStart(qno=int(match.group(1)), page=page_index, y=float(y), source="ocr"))
    return starts


def choose_starts(prefix: str, images: list[Path]) -> list[QStart]:
    starts = text_starts_from_pdf(prefix)
    qset = {s.qno for s in starts}
    if len(qset) < 8:
        starts.extend(ocr_starts_from_images(images))

    # Keep the earliest plausible start for each question number.
    by_q: dict[int, QStart] = {}
    for start in sorted(starts, key=lambda s: (s.qno, s.page, s.y)):
        existing = by_q.get(start.qno)
        if existing is None:
            by_q[start.qno] = start
            continue
        if (start.page, start.y) < (existing.page, existing.y):
            by_q[start.qno] = start
    return sorted(by_q.values(), key=lambda s: (s.page, s.y, s.qno))


def crop_for_question(prefix: str, qno: int, starts: list[QStart], images: list[Path]) -> list[str]:
    current = next((s for s in starts if s.qno == qno), None)
    if current is None:
        return []

    later = [s for s in starts if (s.page, s.y) > (current.page, current.y)]
    next_start = min(later, key=lambda s: (s.page, s.y), default=None)
    end_page = next_start.page if next_start else current.page

    outputs: list[str] = []
    simple = safe_name(prefix)
    for page_index in range(current.page, end_page + 1):
        image = Image.open(images[page_index])
        width, height = image.size
        left = max(0, int(width * 0.045))
        right = min(width, int(width * 0.955))
        top = int(current.y) - 26 if page_index == current.page else int(height * 0.08)
        if next_start and page_index == next_start.page:
            bottom = int(next_start.y) - 18
        else:
            bottom = int(height * 0.94)

        top = max(0, top)
        bottom = min(height, bottom)
        if bottom - top < 80:
            continue

        suffix = "" if page_index == current.page else f"_p{page_index + 1}"
        out_name = f"{simple}_{qno:02d}_原题{suffix}.png"
        out_path = ATTACHMENTS / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image.crop((left, top, right, bottom)).save(out_path)
        outputs.append(out_name)
    return outputs


def rewrite_note(path: Path, image_names: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = read_frontmatter(text)
    if not frontmatter:
        return
    qno = path.stem.rsplit("-", 1)[-1]
    frontmatter = set_frontmatter_value(frontmatter, "图片核验", "待核验" if image_names else "无图片")
    answer, analysis = answer_and_analysis(body)
    image_block = "\n".join(f"![[attachments/{name}]]" for name in image_names)
    if image_block:
        question_body = (
            f"# 题目 {qno}\n\n"
            "原题局部截图如下。以截图为准核对题干、选项、代码和图表。\n\n"
            f"{image_block}\n\n"
        )
    else:
        question_body = f"# 题目 {qno}\n\n未能自动定位原题局部截图，请人工对照原试卷复核。\n\n"
    new_text = f"{frontmatter}\n{question_body}---\n\n{answer}\n\n---\n\n{analysis}\n"
    path.write_text(new_text, encoding="utf-8", newline="\n")


def build_image_review(items: list[tuple[str, Path, list[str]]]) -> None:
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
    current_prefix = ""
    for prefix, path, images in items:
        if prefix != current_prefix:
            current_prefix = prefix
            lines.extend([f"## {prefix}", ""])
        rel = path.relative_to(ROOT).with_suffix("").as_posix()
        lines.append(f"### [[{rel}]]")
        lines.append("")
        if images:
            for name in images:
                lines.append(f"![[attachments/{name}]]")
                lines.append("")
            lines.append("图片核验：待核验")
        else:
            lines.append("未能自动定位题目局部截图。")
        lines.append("")
    (ROOT / "图片核验.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    review_items: list[tuple[str, Path, list[str]]] = []
    total_images = 0
    for prefix in PREFIXES:
        images = render_pages(prefix)
        starts = choose_starts(prefix, images)
        print(f"{prefix}: rendered {len(images)} page(s), detected {len(starts)} question starts")
        for path in note_paths(prefix):
            qno = question_number(path)
            image_names = crop_for_question(prefix, qno, starts, images)
            rewrite_note(path, image_names)
            review_items.append((prefix, path, image_names))
            total_images += len(image_names)
    build_image_review(review_items)
    print(f"rewrote {len(review_items)} notes, created/reused {total_images} image reference(s)")


if __name__ == "__main__":
    main()
