"""Проверка подключения к БД. Запуск: python scripts/check_db.py"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")

from _bootstrap import add_project_root

add_project_root()

from sqlalchemy import create_engine, text

from app.core.config import settings


def check(url: str, label: str) -> bool:
    print(f"\n--- {label} ---")
    print(f"URL: {url}")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("OK: подключение успешно")
        return True
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return False


if __name__ == "__main__":
    ok = check(settings.database_url, "текущий .env")
    if not settings.database_url.startswith("postgresql"):
        print("\nВ .env ожидается PostgreSQL (postgresql+psycopg://...).")
        ok = False
    raise SystemExit(0 if ok else 1)
