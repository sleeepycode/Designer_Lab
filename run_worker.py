"""
Celery worker runner script
Usage: python run_worker.py
"""
import os
import sys
from celery import Celery

# Добавить текущую директорию в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery import celery_app
from app.workers import tasks  # noqa: F401 - Import to register tasks


def run_worker():
    """Запустить Celery worker"""
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--pool=solo',
        '--max-tasks-per-child=1000',
    ])


if __name__ == '__main__':
    run_worker()
