from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

<<<<<<< HEAD
    app_name: str = 'Lab Formatter MVP'
    debug: bool = True
=======
    app_name: str = 'Document Processing Service'
    debug: bool = True
    port: int = 8001

    # Celery with SQLAlchemy backend
    celery_broker_url: str = 'sqla+sqlite:///./celery_broker.db'
    celery_result_backend: str = 'db+sqlite:///./celery_results.db'

    # API Key для аутентификации
    api_key: str = 'your-secret-api-key-change-in-env'

    # Main Backend callback
    main_backend_url: str = 'http://localhost:8000'
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)

    storage_dir: str = 'storage'
    input_dir: str = 'storage/inputs'
    output_dir: str = 'storage/outputs'
    report_dir: str = 'storage/reports'

    university_name: str = """МИНИСТЕРСТВО ЦИФРОВОГО РАЗВИТИЯ, СВЯЗИ И МАССОВЫХ КОММУНИКАЦИЙ РОССИЙСКОЙ ФЕДЕРАЦИИ
Ордена трудового Красного Знамени федеральное государственное бюджетное
образовательное учреждение высшего образования
«Московский технический университет связи и информатики»"""
    city: str = 'Москва'
    year: int = 2026

    # Жестко зафиксированные параметры оформления
    font_name: str = 'Times New Roman'
    font_size_pt: float = 14.0
    line_spacing: float = 1.5
    first_line_indent_cm: float = 1.25

    margin_left_cm: float = 3.0
    margin_right_cm: float = 1.5
    margin_top_cm: float = 2.0
    margin_bottom_cm: float = 2.0


settings = Settings()


def ensure_dirs() -> None:
    for path in [settings.storage_dir, settings.input_dir, settings.output_dir, settings.report_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)
