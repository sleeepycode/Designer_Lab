from fastapi import FastAPI

from app.api.tasks import router as tasks_router
from app.core.config import settings, ensure_dirs
from app.core.db import Base, engine


def create_app() -> FastAPI:
    ensure_dirs()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(tasks_router)

    @app.get('/health')
    def healthcheck():
        return {'status': 'ok'}

    return app


app = create_app()
