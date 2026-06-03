from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_name: str = 'Document Processing Service'
    debug: bool = True
    port: int = 8000


    service_url: str = 'http://127.0.0.1:8000'

    ml_service_url: str = 'http://127.0.0.1:8001'
    ml_timeout: int = 900

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
