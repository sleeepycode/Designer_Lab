<<<<<<< HEAD
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.task import DocumentTask, TaskStatus
from app.schemas.task import TaskCreateResponse, TaskStatusResponse
from app.services.storage import save_input_file, get_output_path, get_report_path
from app.services.validator import validate_source_document
from app.services.gost_formatter import process_document
from app.services.reporting import save_report

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post('', response_model=TaskCreateResponse)
def create_task(
    file: UploadFile = File(...),
    faculty: str = Form(...),
    department: str = Form(...),
=======
# Deprecated: используйте app.api.documents вместо этого

def create_task(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    faculty: str = Form(...),
    department: str = Form(...),
    student_group: str = Form(...),
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    lab_title: str = Form(...),
    lab_number: str = Form(...),
    student_name: str = Form(...),
    reviewer_name: str = Form(...),
<<<<<<< HEAD
    discipline: str =  Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith('.docx'):
=======
    discipline: str =  Form(...),    images: str | None = Form(default=None),  # JSON string of images    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith('.docx'):
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
        raise HTTPException(status_code=400, detail='Поддерживается только формат DOCX.')

    payload = {
        'faculty': faculty,
        'department': department,
<<<<<<< HEAD
=======
        'student_group': student_group,
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
        'lab_title': lab_title,
        'lab_number': lab_number,
        'student_name': student_name,
        'reviewer_name': reviewer_name,
        'discipline': discipline,
<<<<<<< HEAD
    }

    task = DocumentTask(
=======
        'images': json.loads(images) if images else [],
    }

    task = DocumentTask(
        user_id=user_id,
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
        original_filename=file.filename,
        input_path='',
        payload=payload,
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
<<<<<<< HEAD
=======
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ['Входной файл пустой.']
        db.commit()
        raise HTTPException(status_code=400, detail='Входной файл пустой.')

>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    output_path = get_output_path(task.id)
    report_path = get_report_path(task.id)

    task.input_path = input_path

<<<<<<< HEAD
    validation = validate_source_document(input_path)
=======
    try:
        validation = validate_source_document(input_path)
    except Exception:
        task.status = TaskStatus.FAILED
        task.errors = ['Не удалось прочитать DOCX. Проверьте, что файл не поврежден.']
        db.commit()
        raise HTTPException(status_code=400, detail='Не удалось прочитать DOCX. Проверьте, что файл не поврежден.')
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    if not validation['is_valid']:
        report = {
            'status': 'failed',
            'errors': validation['errors'],
            'warnings': validation['warnings'],
            'metrics': validation['metrics'],
            'fixes': [],
        }
        save_report(report_path, report)
        task.status = TaskStatus.FAILED
        task.report_path = report_path
        task.errors = validation['errors']
        task.warnings = validation['warnings']
        db.commit()
        return TaskCreateResponse(task_id=task.id, status=task.status.value, report=report)

<<<<<<< HEAD
    report = process_document(input_path, output_path, payload)
=======
    try:
        report = process_document(input_path, output_path, payload)
    except Exception:
        task.status = TaskStatus.FAILED
        task.errors = ['Ошибка обработки документа. Проверьте входной файл.']
        db.commit()
        raise HTTPException(status_code=400, detail='Ошибка обработки документа. Проверьте входной файл.')
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    report['metrics'] = validation['metrics']
    report['warnings'].extend(validation['warnings'])
    save_report(report_path, report)

    task.status = TaskStatus.COMPLETED
    task.output_path = output_path
    task.report_path = report_path
    task.errors = report['errors']
    task.warnings = report['warnings']
    db.commit()

    return TaskCreateResponse(task_id=task.id, status=task.status.value, report=report)


<<<<<<< HEAD
=======
@router.get('', response_model=TaskHistoryResponse)
def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(DocumentTask)
    if user_id:
        stmt = stmt.where(DocumentTask.user_id == user_id)
    stmt = stmt.order_by(DocumentTask.created_at.desc()).limit(limit)
    tasks = db.execute(stmt).scalars().all()
    items = [
        TaskHistoryItem(
            task_id=task.id,
            user_id=task.user_id,
            status=task.status.value,
            original_filename=task.original_filename,
            created_at=task.created_at,
            has_output=bool(task.output_path),
            has_report=bool(task.report_path),
        )
        for task in tasks
    ]
    return TaskHistoryResponse(items=items)


>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
@router.get('/{task_id}', response_model=TaskStatusResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена.')

    return TaskStatusResponse(
        task_id=task.id,
<<<<<<< HEAD
=======
        user_id=task.user_id,
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
        status=task.status.value,
        errors=task.errors or [],
        warnings=task.warnings or [],
        has_output=bool(task.output_path),
        has_report=bool(task.report_path),
    )


@router.get('/{task_id}/download')
<<<<<<< HEAD
def download_result(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task or not task.output_path:
        raise HTTPException(status_code=404, detail='Готовый файл не найден.')
=======
def download_result(
    task_id: str,
    user_id: str = Query(..., description='Идентификатор пользователя'),
    db: Session = Depends(get_db),
):
    task = db.get(DocumentTask, task_id)
    if not task or not task.output_path:
        raise HTTPException(status_code=404, detail='Готовый файл не найден.')
    if not task.user_id:
        raise HTTPException(status_code=403, detail='У задачи не задан владелец. Скачивание запрещено.')
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail='Нельзя скачать файл другой пользователя.')
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    return FileResponse(task.output_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f'{task_id}.docx')


@router.get('/{task_id}/report')
<<<<<<< HEAD
def download_report(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task or not task.report_path:
        raise HTTPException(status_code=404, detail='Отчёт не найден.')
    return FileResponse(task.report_path, media_type='application/json', filename=f'{task_id}.json')
=======
def download_report(
    task_id: str,
    user_id: str = Query(..., description='Идентификатор пользователя'),
    db: Session = Depends(get_db),
):
    task = db.get(DocumentTask, task_id)
    if not task or not task.report_path:
        raise HTTPException(status_code=404, detail='Отчёт не найден.')
    if not task.user_id:
        raise HTTPException(status_code=403, detail='У задачи не задан владелец. Скачивание отчёта запрещено.')
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail='Нельзя скачать отчёт другой пользователя.')
    return FileResponse(task.report_path, media_type='application/json', filename=f'{task_id}.json')


@router.delete('/{task_id}', response_model=TaskDeleteResponse)
def delete_task(
    task_id: str,
    user_id: str = Query(..., description='Идентификатор пользователя'),
    db: Session = Depends(get_db),
):
    task = db.get(DocumentTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена.')
    if not task.user_id:
        raise HTTPException(status_code=403, detail='У задачи не задан владелец. Удаление запрещено.')
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail='Нельзя удалить задачу другого пользователя.')

    for file_path in [task.input_path, task.output_path, task.report_path]:
        if file_path:
            path = Path(file_path)
            if path.exists():
                path.unlink()

    db.delete(task)
    db.commit()
    return TaskDeleteResponse(task_id=task_id, status='deleted')


@router.post('/extract', response_model=dict)
def extract_docx(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Поддерживается только формат DOCX.')

    task = DocumentTask(
        user_id=user_id,
        original_filename=file.filename,
        input_path='',
        payload={},
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ['Входной файл пустой.']
        db.commit()
        raise HTTPException(status_code=400, detail='Входной файл пустой.')

    output_dir = Path(settings.storage_dir) / 'extracted' / str(task.id)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        content = extract_docx_content(input_path, str(output_dir))
        task.status = TaskStatus.COMPLETED
        db.commit()
        return content
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.errors = [str(e)]
        db.commit()
        raise HTTPException(status_code=400, detail=f'Ошибка извлечения: {str(e)}')


@router.post('/apply-gost')
def apply_gost(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Поддерживается только формат DOCX.')

    task = DocumentTask(
        user_id=user_id,
        original_filename=file.filename,
        input_path='',
        payload={},
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ['Входной файл пустой.']
        db.commit()
        raise HTTPException(status_code=400, detail='Входной файл пустой.')

    output_path = get_output_path(task.id)

    try:
        from app.services.gost_applier import apply_gost_formatting
        apply_gost_formatting(input_path, output_path)
        task.status = TaskStatus.COMPLETED
        task.output_path = output_path
        db.commit()
        return FileResponse(output_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f'{task.id}_gost.docx')
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.errors = [str(e)]
        db.commit()
        raise HTTPException(status_code=400, detail=f'Ошибка применения ГОСТ: {str(e)}')


@router.post('/generate-title')
def generate_title(
    file: UploadFile = File(...),
    department: str = Form(...),
    discipline: str = Form(...),
    lab_number: str = Form(...),
    topic: str = Form(...),
    full_name: str = Form(...),
    group: str = Form(...),
    teacher: str = Form(...),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Поддерживается только формат DOCX.')

    task = DocumentTask(
        user_id=user_id,
        original_filename=file.filename,
        input_path='',
        payload={
            'department': department,
            'discipline': discipline,
            'lab_number': lab_number,
            'topic': topic,
            'full_name': full_name,
            'group': group,
            'teacher': teacher,
        },
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ['Входной файл пустой.']
        db.commit()
        raise HTTPException(status_code=400, detail='Входной файл пустой.')

    output_path = get_output_path(task.id)

    try:
        generate_title_page(input_path, output_path, department, discipline, lab_number, topic, full_name, group, teacher)
        task.status = TaskStatus.COMPLETED
        task.output_path = output_path
        db.commit()
        return FileResponse(output_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f'{task.id}_with_title.docx')
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.errors = [str(e)]
        db.commit()
        raise HTTPException(status_code=400, detail=f'Ошибка генерации титульного листа: {str(e)}')
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
