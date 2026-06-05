from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .imports import commit_import, create_import, load_state, update_draft
from .models import DraftUpdate, ExportRequest, ProgressUpdate
from .question_bank import (
    ROOT,
    detail_for,
    filter_questions,
    find_question,
    metadata,
    question_prompt,
    section_text,
    update_progress,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Question Bank Web", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/vault", StaticFiles(directory=ROOT), name="vault")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/metadata")
def api_metadata() -> dict:
    return metadata()


@app.get("/api/questions")
def api_questions(
    paper: str | None = None,
    knowledge: str | None = None,
    type: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[dict]:
    return filter_questions(paper=paper, knowledge=knowledge, question_type=type, status=status, q=q)


@app.get("/api/questions/{question_id}")
def api_question(question_id: str) -> dict:
    question = find_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return detail_for(question)


@app.put("/api/questions/{question_id}/progress")
def api_update_progress(question_id: str, payload: ProgressUpdate) -> dict:
    try:
        return update_progress(question_id, payload.model_dump(by_alias=True, exclude_none=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Question not found") from None


def store_upload(upload: UploadFile, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "upload.pdf").suffix or ".pdf"
    target = folder / f"{Path(upload.filename or 'upload').stem}{suffix}"
    with target.open("wb") as out:
        shutil.copyfileobj(upload.file, out)
    return target


@app.post("/api/imports")
def api_create_import(
    paper_pdf: Annotated[UploadFile, File()],
    answer_pdf: Annotated[UploadFile | None, File()] = None,
    year_month: Annotated[str, Form()] = "",
    organization: Annotated[str, Form()] = "",
    exam_type: Annotated[str, Form()] = "",
    force_ocr: Annotated[bool, Form()] = True,
) -> dict:
    if not year_month or not organization or not exam_type:
        raise HTTPException(status_code=400, detail="year_month, organization, and exam_type are required")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        paper_path = store_upload(paper_pdf, tmp_dir)
        answer_path = store_upload(answer_pdf, tmp_dir) if answer_pdf else None
        try:
            return create_import(
                paper_pdf=paper_path,
                answer_pdf=answer_path,
                year_month=year_month,
                organization=organization,
                exam_type=exam_type,
                force_ocr=force_ocr,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/imports/{import_id}")
def api_get_import(import_id: str) -> dict:
    try:
        return load_state(import_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Import not found") from None


@app.put("/api/imports/{import_id}/drafts/{draft_id}")
def api_update_draft(import_id: str, draft_id: str, payload: DraftUpdate) -> dict:
    try:
        return update_draft(import_id, draft_id, payload.model_dump(exclude_none=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Draft not found") from None


@app.post("/api/imports/{import_id}/commit")
def api_commit_import(import_id: str) -> dict:
    try:
        result = commit_import(import_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Import not found") from None
    if result["errors"]:
        raise HTTPException(status_code=409, detail=result)
    return result


@app.post("/api/sets/export")
def api_export_set(payload: ExportRequest) -> PlainTextResponse:
    parts = [f"# {payload.title}", ""]
    missing: list[str] = []
    for index, question_id in enumerate(payload.ids, start=1):
        question = find_question(question_id)
        if not question:
            missing.append(question_id)
            continue
        prompt = question_prompt(question.body)
        prompt = prompt.replace("# 题目", f"# {index}. 题目", 1) if prompt.startswith("# 题目") else f"## {index}. {question_id}\n\n{prompt}"
        parts.extend([prompt.strip(), ""])
        if payload.include_answers:
            answer = section_text(question.body, "答案")
            analysis = section_text(question.body, "解析")
            parts.extend(["## 答案", answer.strip(), "", "## 解析", analysis.strip(), ""])
        parts.append("---")
        parts.append("")
    if missing:
        parts.extend(["## 未找到题目", *[f"- {item}" for item in missing], ""])
    markdown = "\n".join(parts).strip() + "\n"
    export_dir = ROOT / "_exports"
    export_dir.mkdir(exist_ok=True)
    output = export_dir / f"练习卷-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    output.write_text(markdown, encoding="utf-8")
    return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8")
