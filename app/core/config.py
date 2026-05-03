from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Lab Formatter MVP'
    debug: bool = True
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    database_url: str = 'postgresql+psycopg://postgres:postgres@localhost:5432/lab_formatter'

    storage_dir: str = 'storage'
    input_dir: str = 'storage/inputs'
    output_dir: str = 'storage/outputs'
    report_dir: str = 'storage/reports'
    projects_dir: str = 'storage/projects'

    # Отдельный процесс gost_module (Designer_Lab ML/gost_module): POST /analyze
    gost_module_base_url: str = ''

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


def get_cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()]


def ensure_dirs() -> None:
    for path in [settings.storage_dir, settings.input_dir, settings.output_dir, settings.report_dir, settings.projects_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)
