from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Lab Formatter MVP'
    debug: bool = True
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    database_url: str = 'sqlite:///./lab_formatter.db'

    storage_dir: str = 'storage'
    input_dir: str = 'storage/inputs'
    output_dir: str = 'storage/outputs'
    report_dir: str = 'storage/reports'
    projects_dir: str = 'storage/projects'

    doc_service_base_url: str = 'https://sleeepycode-designer-lab-1dc4.twc1.net'
    doc_service_timeout: int = 900
    ml_service_base_url: str = ''
    ml_timeout: int = 900

    # Публичный URL backend №1 — для images[].path (ML и doc-service скачивают по HTTP)
    backend_public_url: str = 'http://127.0.0.1:8002'

    auth_secret_key: str = 'change-me-in-production'
    auth_token_expire_minutes: int = 60 * 24 * 7


settings = Settings()


def get_cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()]


def ensure_dirs() -> None:
    for path in [settings.storage_dir, settings.input_dir, settings.output_dir, settings.report_dir, settings.projects_dir]:
        Path(path).mkdir(parents=True, exist_ok=True)
