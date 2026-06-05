"""Проверка подключения к БД. Запуск: python scripts/check_db.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.db import check_db_connection, init_db


def main() -> int:
    print(f"database_url = {settings.database_url}")
    try:
        check_db_connection()
        init_db()
        print("OK: подключение к БД работает, таблицы на месте.")
        return 0
    except Exception as exc:
        print(f"Ошибка: {exc}")
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
