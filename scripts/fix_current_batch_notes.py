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

FOLDER_TAG = {
    "01数据与编码": "01数据与编码",
    "02算法": "02算法",
    "03python基础": "03python基础",
    "04数据处理": "04数据处理",
    "05人工智能": "05人工智能",
    "06信息系统": "06信息系统",
    "07信息安全": "07信息安全",
    "08数组": "08数组",
    "09队列": "09队列",
    "10栈": "10栈",
    "11链表": "11链表",
    "12树": "12树",
    "13查找与排序": "13查找与排序",
    "14迭代与递归": "14迭代与递归",
}


def is_current_batch_note(path: Path) -> bool:
    name = path.stem
    return any(name.startswith(prefix + "-") for prefix in PREFIXES)


def parse_id(path: Path) -> tuple[str, str, str]:
    stem = path.stem
    qno = stem.rsplit("-", 1)[-1]
    prefix = stem[: -(len(qno) + 1)]
    grade = prefix.split("-")[-2]
    return stem, prefix, qno


def extract_body(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].lstrip()
    return text


def extract_answer(body: str) -> str:
    patterns = [
        r"\*\*正确答案：\*\*\s*([^\n]+)",
        r"\*\*\?+\*\*\s*([^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body)
        if match:
            value = match.group(1).strip()
            return value or "见答案解析"
    return "见答案解析"


def clean_question_body(body: str, qno: str) -> str:
    body = re.sub(r"^#\s*\?+\s*\d+\s*", "", body, flags=re.M)
    body = re.sub(r"^#\s*题目\s*\d+\s*", "", body, flags=re.M)
    body = re.sub(r"(\n\s*){2,}#\s*题目\s*\d+\s*", "\n\n", body)
    body = re.split(r"\n---\s*\n\s*##\s*\?+", body, maxsplit=1)[0]
    body = re.split(r"\n---\s*\n\s*##\s*答案", body, maxsplit=1)[0]
    body = body.strip()
    if not body:
        body = f"第 {int(qno)} 题题干见原试卷。"
    return body


def difficulty(qno: str) -> str:
    number = int(qno)
    if number <= 8:
        return "简单"
    if number <= 12:
        return "中等"
    return "困难"


def question_type(qno: str) -> str:
    return "选择题" if int(qno) <= 12 else "填空题"


def make_note(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    body = extract_body(text)
    note_id, prefix, qno = parse_id(path)
    grade = prefix.split("-")[-2]
    folder = path.parent.name
    knowledge = FOLDER_TAG.get(folder, folder)
    answer = extract_answer(body)
    answer = re.sub(r"\?{2,}", "；", answer).strip("； ")
    answer = re.sub(r"\?+", "；", answer).strip("； ")
    if not answer or answer.upper().startswith("OCR"):
        answer = "OCR 识别不可靠，见原答案复核"
    question = clean_question_body(body, qno)
    question = re.sub(
        r"OCR\s+\?+\s+(\d{2})\s+\?+",
        r"OCR 未能可靠识别第 \1 题题干，请对照原试卷复核。",
        question,
    )
    question = re.sub(r"\?{2,}", "；", question)
    pdf_name = f"{prefix}.pdf"

    frontmatter = "\n".join(
        [
            "---",
            f"id: {note_id}",
            f"题型: {question_type(qno)}",
            f"来源: \"[[试卷/{pdf_name}|{pdf_name}]]\"",
            f"试卷: {pdf_name}",
            f"年级: {grade}",
            f"题号: \"{qno}\"",
            f"难度: {difficulty(qno)}",
            "知识点:",
            f"  - {knowledge}",
            "完成次数: 0",
            "正确率:",
            "状态: 未练习",
            "错题原因:",
            "创建日期: 2026-06-11",
            "图片核验: 无图片",
            "tags:",
            "  - 状态/未练习",
            f"  - 知识点/{knowledge}",
            "---",
            "",
        ]
    )

    return (
        frontmatter
        + f"# 题目 {qno}\n\n"
        + question
        + "\n\n---\n\n"
        + "## 答案\n\n"
        + f"**正确答案：** {answer}\n\n"
        + "---\n\n"
        + "## 解析\n\n"
        + "依据原卷与参考答案整理。OCR 识别题请复核题干细节、代码缩进和图表内容。\n\n"
        + "---\n\n"
        + "## 相关链接\n\n"
        + f"- 原试卷：[[试卷/{pdf_name}|{pdf_name}]]\n"
    )


def main() -> None:
    changed = 0
    for path in ROOT.rglob("*.md"):
        if not is_current_batch_note(path):
            continue
        path.write_text(make_note(path), encoding="utf-8", newline="\n")
        changed += 1
    print(f"rewrote {changed} notes")


if __name__ == "__main__":
    main()
