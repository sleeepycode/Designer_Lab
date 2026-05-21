"""Единый JSON ошибок для фронта (см. frontend/docs/API_CONTRACT.md)."""

from fastapi import HTTPException


def raise_api_error(
    code: str,
    message: str,
    status_code: int = 400,
    details: object | None = None,
) -> None:
    payload: dict = {'code': code, 'message': message}
    if details is not None:
        payload['details'] = details
    raise HTTPException(status_code=status_code, detail=payload)


def require_docx_upload(filename: str | None) -> None:
    if not filename or not filename.lower().endswith('.docx'):
        raise_api_error(
            'invalid_file_format',
            'Некорректный формат файла. Поддерживается только DOCX.',
        )


def require_image_upload(filename: str | None) -> None:
    if not filename:
        raise_api_error('invalid_file_format', 'Имя файла отсутствует.')
    ext = filename.lower()
    if not ext.endswith(('.png', '.jpg', '.jpeg')):
        raise_api_error(
            'invalid_file_format',
            'Некорректный формат файла. Для доп. загрузки поддерживаются только PNG и JPG.',
        )
