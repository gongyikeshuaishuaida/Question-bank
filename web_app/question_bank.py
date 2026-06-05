from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
QUESTION_DIR_RE = re.compile(r"^\d{2}")
FIELD_ALIASES = {
    "完成次数": "完成次数",
    "正确率": "正确率",
    "状态": "状态",
    "错题原因": "错题原因",
}


@dataclass(frozen=True)
class QuestionFile:
    path: Path
    meta: dict[str, Any]
    body: str

    @property
    def rel_path(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def knowledge_dirs(root: Path = ROOT) -> list[str]:
    return [
        path.name
        for path in sorted(root.iterdir())
        if path.is_dir() and QUESTION_DIR_RE.match(path.name)
    ]


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :].lstrip("\r\n")
    data = yaml.safe_load(raw) or {}
    return data if isinstance(data, dict) else {}, body


def dump_frontmatter(meta: dict[str, Any], body: str) -> str:
    raw = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, width=1000).strip()
    return f"---\n{raw}\n---\n\n{body.lstrip()}"


def read_question(path: Path) -> QuestionFile:
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    return QuestionFile(path=path, meta=meta, body=body)


def iter_question_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for folder in knowledge_dirs(root):
        files.extend(sorted((root / folder).glob("*.md")))
    return files


def read_all_questions(root: Path = ROOT) -> list[QuestionFile]:
    questions: list[QuestionFile] = []
    for path in iter_question_files(root):
        try:
            question = read_question(path)
        except UnicodeDecodeError:
            continue
        if question.meta.get("id"):
            questions.append(question)
    return questions


def section_text(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*$", body, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^## |\n---\n", body[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(body)
    return body[start:end].strip()


def question_prompt(body: str) -> str:
    cut = re.search(r"^## 答案\s*$|^## 解析\s*$", body, flags=re.MULTILINE)
    return body[: cut.start()].strip() if cut else body.strip()


def detail_for(question: QuestionFile) -> dict[str, Any]:
    answer = section_text(question.body, "答案")
    analysis = section_text(question.body, "解析")
    prompt = question_prompt(question.body)
    return {
        **summary_for(question),
        "body": prompt,
        "answer": answer,
        "analysis": analysis,
        "html": markdown_to_html(prompt),
        "answer_html": markdown_to_html(answer),
        "analysis_html": markdown_to_html(analysis),
        "meta": question.meta,
    }


def summary_for(question: QuestionFile) -> dict[str, Any]:
    meta = question.meta
    knowledge = meta.get("知识点") or []
    if isinstance(knowledge, str):
        knowledge = [knowledge]
    prompt = question_prompt(question.body)
    first_text = re.sub(r"\s+", " ", re.sub(r"!\[\[[^\]]+\]\]", "", prompt)).strip()
    return {
        "id": meta.get("id", question.path.stem),
        "path": question.rel_path,
        "title": prompt.splitlines()[0].strip("# ").strip() if prompt else question.path.stem,
        "excerpt": first_text[:180],
        "paper": meta.get("试卷", ""),
        "number": str(meta.get("题号", "")),
        "type": meta.get("题型", ""),
        "difficulty": meta.get("难度", ""),
        "knowledge": knowledge,
        "status": meta.get("状态", ""),
        "completed_count": meta.get("完成次数", 0),
        "accuracy": meta.get("正确率", ""),
        "image_check": meta.get("图片核验", ""),
    }


def find_question(question_id: str, root: Path = ROOT) -> QuestionFile | None:
    for question in read_all_questions(root):
        if question.meta.get("id") == question_id:
            return question
    return None


def filter_questions(
    paper: str | None = None,
    knowledge: str | None = None,
    question_type: str | None = None,
    status: str | None = None,
    q: str | None = None,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    needle = (q or "").strip().lower()
    rows: list[dict[str, Any]] = []
    for question in read_all_questions(root):
        summary = summary_for(question)
        if paper and summary["paper"] != paper:
            continue
        if knowledge and knowledge not in summary["knowledge"]:
            continue
        if question_type and summary["type"] != question_type:
            continue
        if status and summary["status"] != status:
            continue
        if needle:
            haystack = f"{summary['id']} {summary['paper']} {summary['excerpt']} {' '.join(summary['knowledge'])}".lower()
            if needle not in haystack:
                continue
        rows.append(summary)
    return sorted(rows, key=lambda item: (item["paper"], item["number"], item["id"]))


def metadata(root: Path = ROOT) -> dict[str, Any]:
    questions = read_all_questions(root)
    summaries = [summary_for(question) for question in questions]
    return {
        "knowledge": knowledge_dirs(root),
        "papers": sorted({item["paper"] for item in summaries if item["paper"]}),
        "types": sorted({item["type"] for item in summaries if item["type"]}),
        "statuses": sorted({item["status"] for item in summaries if item["status"]}),
        "difficulties": sorted({item["difficulty"] for item in summaries if item["difficulty"]}),
        "count": len(summaries),
    }


def update_progress(question_id: str, updates: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    question = find_question(question_id, root)
    if not question:
        raise FileNotFoundError(question_id)
    meta = dict(question.meta)
    for key, value in updates.items():
        if value is not None and key in FIELD_ALIASES:
            meta[FIELD_ALIASES[key]] = value
    if meta.get("状态"):
        tags = [tag for tag in meta.get("tags", []) if not str(tag).startswith("状态/")]
        tags.insert(0, f"状态/{meta['状态']}")
        meta["tags"] = tags
    question.path.write_text(dump_frontmatter(meta, question.body), encoding="utf-8")
    return detail_for(read_question(question.path))


def obsidian_image_to_url(match: re.Match[str]) -> str:
    raw = match.group(1)
    path = raw
    if "|" in path:
        path = path.split("|", 1)[0]
    path = path.strip()
    return f'<img src="/vault/{html.escape(path)}" alt="{html.escape(Path(path).name)}">'


def inline_format(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    markdown = re.sub(r"!\[\[([^\]]+)\]\]", obsidian_image_to_url, markdown)
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False
    code_lines: list[str] = []
    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{'<br>'.join(inline_format(line) for line in para)}</p>")
            para.clear()

    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_para()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_para()
            continue
        if line.startswith("<img "):
            flush_para()
            out.append(line)
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_para()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline_format(heading.group(2))}</h{level}>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            flush_para()
            content = re.sub(r"^\s*[-*]\s+", "", line)
            out.append(f"<p class=\"option\">{inline_format(content)}</p>")
            continue
        para.append(line)
    flush_para()
    if in_code:
        out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(out)


def write_question_note(
    *,
    paper_stem: str,
    draft: dict[str, Any],
    source_pdf_name: str,
    root: Path = ROOT,
) -> Path:
    number = f"{int(str(draft['number'])):02d}" if str(draft["number"]).isdigit() else str(draft["number"])
    question_id = f"{paper_stem}-{number}"
    knowledge = draft.get("knowledge") or ["03python基础"]
    primary = knowledge[0]
    folder = root / primary
    if not folder.exists():
        raise FileNotFoundError(f"Knowledge folder not found: {primary}")
    target = folder / f"{question_id}.md"
    if target.exists():
        raise FileExistsError(target)

    today = draft.get("created_date") or ""
    image_check = draft.get("image_check") or ("待核验" if draft.get("image_names") else "无图片")
    tags = [f"状态/未练习", *[f"知识点/{item}" for item in knowledge]]
    meta = {
        "id": question_id,
        "题型": draft.get("question_type") or "选择题",
        "来源": f"[[试卷/{source_pdf_name}|{source_pdf_name}]]",
        "试卷": source_pdf_name,
        "题号": number,
        "难度": draft.get("difficulty") or "中等",
        "知识点": knowledge,
        "完成次数": 0,
        "正确率": None,
        "状态": "未练习",
        "错题原因": None,
        "创建日期": today,
        "图片核验": image_check,
        "tags": tags,
    }
    body = normalize_body(number, draft.get("body") or "", draft.get("answer") or "", draft.get("analysis") or "")
    target.write_text(dump_frontmatter(meta, body), encoding="utf-8")
    return target


def normalize_body(number: str, body: str, answer: str, analysis: str) -> str:
    prompt = body.strip()
    if not prompt.startswith("# "):
        prompt = f"# 题目 {number}\n\n{prompt}"
    answer_text = answer.strip() or "待审核"
    if not answer_text.startswith("**正确答案"):
        answer_text = f"**正确答案：** {answer_text}"
    analysis_text = analysis.strip() or "待审核"
    return f"{prompt}\n\n---\n\n## 答案\n\n{answer_text}\n\n---\n\n## 解析\n\n{analysis_text}\n\n---\n\n## 相关链接\n"
