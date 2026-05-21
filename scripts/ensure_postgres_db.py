"""
Создать БД lab_formatter, если её ещё нет.
Запуск из корня проекта: python scripts/ensure_postgres_db.py

Подключение к служебной БД postgres — из DATABASE_URL в .env
(имя базы в URL заменяется на postgres).
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")

from _bootstrap import add_project_root

add_project_root()

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from app.core.config import settings


def _admin_url() -> str:
    url = make_url(settings.database_url)
    return str(url.set(database="postgres"))


def main() -> int:
    target = make_url(settings.database_url).database
    print(f"Проверка PostgreSQL, база: {target}")
    admin = create_engine(_admin_url(), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{target}"'))
                print(f"Создана база: {target}")
            else:
                print(f"База уже есть: {target}")
    except Exception as exc:
        print(f"Ошибка: {exc}")
        print("Проверьте пароль в .env (postgres:postgres → ваш пароль при установке).")
        return 1

    app_engine = create_engine(settings.database_url)
    try:
        with app_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Подключение к lab_formatter: OK")
    except Exception as exc:
        print(f"Подключение к {target}: FAIL — {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
