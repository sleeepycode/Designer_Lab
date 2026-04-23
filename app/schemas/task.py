from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class TitlePagePayload(BaseModel):
    faculty: str = Field(..., description='Факультет')
    department: str = Field(..., description='Кафедра')
    lab_title: str = Field(..., description='Название лабораторной работы')
    lab_number: str = Field(..., description='Номер лабораторной работы')
    student_group: str = Field(..., description='Учебная группа студента')
    student_name: str = Field(..., description='ФИО студента')
    reviewer_name: str = Field(..., description='ФИО проверяющего')
    discipline: str = Field(..., description='Дисциплина')


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    report: dict[str, Any]


class TaskStatusResponse(BaseModel):
    task_id: str
    user_id: str | None = None
    status: str
    errors: list[str] = []
    warnings: list[str] = []
    has_output: bool = False
    has_report: bool = False


class TaskHistoryItem(BaseModel):
    task_id: str
    user_id: str | None = None
    status: str
    original_filename: str
    created_at: datetime
    has_output: bool
    has_report: bool


class TaskHistoryResponse(BaseModel):
    items: list[TaskHistoryItem]


class TaskDeleteResponse(BaseModel):
    task_id: str
    status: str
