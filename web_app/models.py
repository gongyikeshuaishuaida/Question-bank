from __future__ import annotations

from pydantic import BaseModel, Field


class ProgressUpdate(BaseModel):
    completed_count: int | None = Field(default=None, alias="完成次数")
    accuracy: str | float | None = Field(default=None, alias="正确率")
    status: str | None = Field(default=None, alias="状态")
    mistake_reason: str | None = Field(default=None, alias="错题原因")

    model_config = {"populate_by_name": True}


class DraftImage(BaseModel):
    page: int
    box: list[int]
    label: str = "图1"


class DraftUpdate(BaseModel):
    body: str | None = None
    answer: str | None = None
    analysis: str | None = None
    question_type: str | None = None
    number: str | None = None
    difficulty: str | None = None
    knowledge: list[str] | None = None
    image_check: str | None = None
    images: list[DraftImage] | None = None
    accepted: bool | None = None


class ExportRequest(BaseModel):
    ids: list[str]
    include_answers: bool = False
    title: str = "练习卷"
