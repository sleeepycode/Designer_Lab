"""
FastAPI server runner script
Usage: python run_server.py
"""
import os
import sys
import uvicorn

# Добавить текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


if __name__ == '__main__':
    uvicorn.run(
        "app.main:create_app",
        host='0.0.0.0',
        port=settings.port,
        reload=settings.debug,
        factory=True,
        reload_dirs=["./app"],  # ✅ Следить только за папкой app
        reload_excludes=[".venv", "__pycache__", "*.pyc"],  # ✅ Исключить .venv
    )