from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import fitz
from PIL import Image

from .question_bank import ROOT, knowledge_dirs, write_question_note


IMPORT_ROOT = ROOT / "_web_imports"
PAGE_SCALE = 2.6
OCR_LANGS = ["ch_sim", "en"]

KEYWORD_KNOWLEDGE: list[tuple[str, str]] = [
    ("RFID|编码|二进制|数据|信息|大数据", "01数据与编码"),
    ("算法|流程图|有限性|确定性|输入|输出", "02算法"),
    ("Python|列表|字典|字符串|range|for |while |def |random|代码", "03python基础"),
    ("Excel|pandas|DataFrame|read_excel|groupby|图表|数据处理", "04数据处理"),
    ("人工智能|机器学习|神经网络|模型|训练", "05人工智能"),
    ("信息系统|服务器|浏览器|APP|传感器|数据库|系统", "06信息系统"),
    ("安全|加密|解密|认证|病毒|防火墙|权限|备份", "07信息安全"),
    ("数组|下标|索引|前缀和", "08数组"),
    ("队列|队首|队尾|循环队列|front|rear", "09队列"),
    ("栈|入栈|出栈|单调栈|stack", "10栈"),
    ("链表|head|指针|节点|next", "11链表"),
    ("树|二叉树|根节点|叶子|遍历", "12树"),
    ("排序|查找|二分|冒泡|选择|插入", "13查找与排序"),
    ("递归|迭代|复杂度", "14迭代与递归"),
]


def import_dir(import_id: str) -> Path:
    return IMPORT_ROOT / import_id


def state_path(import_id: str) -> Path:
    return import_dir(import_id) / "state.json"


def load_state(import_id: str) -> dict[str, Any]:
    path = state_path(import_id)
    if not path.exists():
        raise FileNotFoundError(import_id)
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    path = state_path(state["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def render_pdf(pdf_path: Path, output_dir: Path, prefix: str) -> list[dict[str, Any]]:
    doc = fitz.open(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages: list[dict[str, Any]] = []
    matrix = fitz.Matrix(PAGE_SCALE, PAGE_SCALE)
    for index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        out = output_dir / f"{prefix}_p{index:02d}.png"
        pix.save(out)
        embedded = page.get_text("text").strip()
        pages.append(
            {
                "page": index,
                "image": out.relative_to(ROOT).as_posix(),
                "width": pix.width,
                "height": pix.height,
                "embedded_text": embedded,
                "ocr_text": "",
                "ocr_error": "",
            }
        )
    return pages


def get_easyocr_reader() -> Any:
    import easyocr

    return easyocr.Reader(OCR_LANGS, gpu=False)


def run_ocr_for_pages(pages: list[dict[str, Any]], force_ocr: bool = True) -> None:
    if not force_ocr:
        for page in pages:
            page["ocr_text"] = page.get("embedded_text", "")
        return
    try:
        reader = get_easyocr_reader()
    except Exception as exc:  # OCR can fail before models are available; keep import review usable.
        for page in pages:
            page["ocr_text"] = page.get("embedded_text", "")
            page["ocr_error"] = f"EasyOCR unavailable, used embedded text fallback: {exc}"
        return
    for page in pages:
        try:
            result = reader.readtext(str(ROOT / page["image"]), detail=0, paragraph=True)
            page["ocr_text"] = "\n".join(str(item).strip() for item in result if str(item).strip())
            if not page["ocr_text"].strip():
                page["ocr_text"] = page.get("embedded_text", "")
        except Exception as exc:
            page["ocr_text"] = page.get("embedded_text", "")
            page["ocr_error"] = f"OCR failed, used embedded text fallback: {exc}"


def normalize_ocr_text(pages: list[dict[str, Any]]) -> str:
    chunks = []
    for page in pages:
        text = page.get("ocr_text") or page.get("embedded_text") or ""
        chunks.append(f"\n[第{page['page']}页]\n{text.strip()}")
    return "\n".join(chunks).strip()


def split_question_blocks(text: str) -> list[tuple[str, str]]:
    clean = re.sub(r"\r\n?", "\n", text)
    clean = re.sub(r"[ \t]+", " ", clean)
    patterns = list(re.finditer(r"(?m)^\s*(?:第\s*)?(\d{1,2})\s*[.．、]\s*", clean))
    if not patterns:
        patterns = list(re.finditer(r"(?m)^\s*（?(\d{1,2})）\s*", clean))
    if not patterns:
        return [("01", clean.strip())] if clean.strip() else []

    prefix = clean[: patterns[0].start()].strip()
    blocks: list[tuple[str, str]] = []
    for idx, match in enumerate(patterns):
        end = patterns[idx + 1].start() if idx + 1 < len(patterns) else len(clean)
        number = f"{int(match.group(1)):02d}"
        block = clean[match.start() : end].strip()
        if prefix and looks_like_material(prefix):
            block = f"{prefix}\n\n{block}"
        blocks.append((number, block))
    deduped: list[tuple[str, str]] = []
    seen = set()
    for number, block in blocks:
        if number in seen:
            continue
        seen.add(number)
        deduped.append((number, block))
    return deduped


def looks_like_material(text: str) -> bool:
    return any(marker in text for marker in ["阅读下列材料", "阅读材料", "回答第", "完成选择题"])


def parse_answers(answer_text: str) -> dict[str, str]:
    answers: dict[str, str] = {}
    for match in re.finditer(r"(?:第)?\s*(\d{1,2})\s*(?:题)?\s*[.．、:：]?\s*([A-D](?:[、,， ]+[A-D])?|[（(]?\d+[）)]?.{0,40})", answer_text):
        number = f"{int(match.group(1)):02d}"
        value = match.group(2).strip()
        if value:
            answers.setdefault(number, value)
    return answers


def suggest_knowledge(text: str) -> list[str]:
    suggestions: list[str] = []
    for pattern, knowledge in KEYWORD_KNOWLEDGE:
        if re.search(pattern, text, flags=re.IGNORECASE):
            suggestions.append(knowledge)
    if not suggestions:
        suggestions.append("03python基础" if re.search(r"for|while|列表|程序|代码|____", text, re.I) else "01数据与编码")
    valid = set(knowledge_dirs())
    return [item for item in dict.fromkeys(suggestions) if item in valid] or [knowledge_dirs()[0]]


def infer_question_type(text: str) -> str:
    if "____" in text or "填入" in text or "划线处" in text or re.search(r"①|②|③|④", text):
        return "填空题"
    if re.search(r"(?m)^\s*[- ]?[A-D][.．、]", text):
        return "选择题"
    return "选择题"


def build_drafts(paper_text: str, answer_text: str) -> list[dict[str, Any]]:
    answers = parse_answers(answer_text)
    drafts: list[dict[str, Any]] = []
    for number, block in split_question_blocks(paper_text):
        body = block.strip()
        drafts.append(
            {
                "id": str(uuid.uuid4()),
                "number": number,
                "question_type": infer_question_type(body),
                "difficulty": "中等",
                "knowledge": suggest_knowledge(body),
                "body": f"# 题目 {number}\n\n{body}",
                "answer": answers.get(number, ""),
                "analysis": "",
                "image_check": "无图片",
                "images": [],
                "accepted": True,
            }
        )
    return drafts


def create_import(
    *,
    paper_pdf: Path,
    answer_pdf: Path | None,
    year_month: str,
    organization: str,
    exam_type: str,
    force_ocr: bool = True,
) -> dict[str, Any]:
    import_id = uuid.uuid4().hex[:12]
    base = import_dir(import_id)
    uploads = base / "uploads"
    pages_dir = base / "pages"
    uploads.mkdir(parents=True, exist_ok=True)

    paper_stem = f"{year_month}-{organization}-{exam_type}"
    paper_name = f"{paper_stem}.pdf"
    stored_paper = uploads / paper_name
    shutil.copy2(paper_pdf, stored_paper)

    stored_answer = None
    if answer_pdf:
        stored_answer = uploads / f"{paper_stem}-答案.pdf"
        shutil.copy2(answer_pdf, stored_answer)

    paper_pages = render_pdf(stored_paper, pages_dir, "paper")
    run_ocr_for_pages(paper_pages, force_ocr=force_ocr)
    answer_pages: list[dict[str, Any]] = []
    if stored_answer:
        answer_pages = render_pdf(stored_answer, pages_dir, "answer")
        run_ocr_for_pages(answer_pages, force_ocr=force_ocr)

    paper_text = normalize_ocr_text(paper_pages)
    answer_text = normalize_ocr_text(answer_pages)
    drafts = build_drafts(paper_text, answer_text)
    today = date.today().isoformat()
    for draft in drafts:
        draft["created_date"] = today

    state = {
        "id": import_id,
        "paper_stem": paper_stem,
        "paper_name": paper_name,
        "answer_name": stored_answer.name if stored_answer else "",
        "uploads": {
            "paper": stored_paper.relative_to(ROOT).as_posix(),
            "answer": stored_answer.relative_to(ROOT).as_posix() if stored_answer else "",
        },
        "pages": paper_pages,
        "answer_pages": answer_pages,
        "drafts": drafts,
        "created_date": today,
        "ai_available": bool(os.environ.get("OPENAI_API_KEY")),
    }
    save_state(state)
    return state


def update_draft(import_id: str, draft_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    state = load_state(import_id)
    for draft in state["drafts"]:
        if draft["id"] != draft_id:
            continue
        for key, value in updates.items():
            if value is not None:
                draft[key] = value
        if draft.get("images"):
            draft["image_check"] = draft.get("image_check") or "待核验"
        save_state(state)
        return draft
    raise FileNotFoundError(draft_id)


def crop_draft_images(state: dict[str, Any], draft: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for idx, item in enumerate(draft.get("images", []), start=1):
        page_number = int(item["page"])
        page = next((p for p in state["pages"] if int(p["page"]) == page_number), None)
        if not page:
            continue
        box = tuple(int(v) for v in item["box"])
        if len(box) != 4:
            continue
        source = ROOT / page["image"]
        image = Image.open(source)
        cropped = image.crop(box)
        label = re.sub(r"[^\w\u4e00-\u9fff-]+", "", item.get("label") or f"图{idx}") or f"图{idx}"
        filename = f"{state['paper_stem'].replace('-', '')}_{draft['number']}_{label}.png"
        output = ROOT / "attachments" / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output)
        names.append(filename)
    return names


def inject_images(body: str, image_names: list[str]) -> str:
    if not image_names:
        return body
    embeds = "\n".join(f"![[attachments/{name}]]" for name in image_names)
    lines = body.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join([lines[0], "", embeds, "", *lines[1:]]).strip()
    return f"{embeds}\n\n{body}".strip()


def commit_import(import_id: str) -> dict[str, Any]:
    state = load_state(import_id)
    paper_src = ROOT / state["uploads"]["paper"]
    paper_dst = ROOT / "试卷" / state["paper_name"]
    paper_dst.parent.mkdir(parents=True, exist_ok=True)
    if not paper_dst.exists():
        shutil.copy2(paper_src, paper_dst)
    if state["uploads"].get("answer"):
        answer_src = ROOT / state["uploads"]["answer"]
        answer_dst = ROOT / "试卷" / state["answer_name"]
        if not answer_dst.exists():
            shutil.copy2(answer_src, answer_dst)

    written: list[str] = []
    errors: list[str] = []
    for draft in state["drafts"]:
        if not draft.get("accepted", True):
            continue
        try:
            image_names = crop_draft_images(state, draft)
            draft["image_names"] = image_names
            draft["body"] = inject_images(draft.get("body", ""), image_names)
            if image_names and draft.get("image_check") == "无图片":
                draft["image_check"] = "待核验"
            target = write_question_note(
                paper_stem=state["paper_stem"],
                draft=draft,
                source_pdf_name=state["paper_name"],
            )
            written.append(target.relative_to(ROOT).as_posix())
        except Exception as exc:
            errors.append(f"{draft.get('number')}: {exc}")
    state["commit"] = {"written": written, "errors": errors}
    save_state(state)
    return state["commit"]
