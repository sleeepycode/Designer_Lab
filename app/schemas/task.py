<<<<<<< HEAD
=======
from datetime import datetime
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
from typing import Any
from pydantic import BaseModel, Field


class TitlePagePayload(BaseModel):
    faculty: str = Field(..., description='Факультет')
    department: str = Field(..., description='Кафедра')
    lab_title: str = Field(..., description='Название лабораторной работы')
    lab_number: str = Field(..., description='Номер лабораторной работы')
<<<<<<< HEAD
    student_name: str = Field(..., description='ФИО студента')
    reviewer_name: str = Field(..., description='ФИО проверяющего')
    discipline: str = Field(..., description='Дисциплина')


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    report: dict[str, Any]
=======
    student_group: str = Field(..., description='Учебная группа студента')
    student_name: str = Field(..., description='ФИО студента')
    reviewer_name: str = Field(..., description='ФИО проверяющего')
    discipline: str = Field(..., description='Дисциплина')
    images: list[dict] = Field(default_factory=list, description='Список изображений для вставки')


class ProcessDocumentRequest(BaseModel):
    title_page: TitlePagePayload = Field(..., description='Данные титульной страницы')


class ProcessDocumentResponse(BaseModel):
    task_id: str
    status: str
    message: str
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
<<<<<<< HEAD
=======
    original_filename: str
    created_at: datetime
    updated_at: datetime
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    errors: list[str] = []
    warnings: list[str] = []
    has_output: bool = False
    has_report: bool = False
<<<<<<< HEAD
=======


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] | None = None
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
