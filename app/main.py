from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.tasks import router as tasks_router
from app.core.config import settings, ensure_dirs
from app.core.db import Base, engine, ensure_schema_compatibility


def create_app() -> FastAPI:
    ensure_dirs()
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(tasks_router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            code = str(exc.detail.get('code', f'http_{exc.status_code}'))
            message = str(exc.detail.get('message', 'HTTP error'))
            details = exc.detail.get('details')
        else:
            code = f'http_{exc.status_code}'
            message = str(exc.detail)
            details = None
        return JSONResponse(
            status_code=exc.status_code,
            content={'code': code, 'message': message, 'details': details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                'code': 'validation_error',
                'message': 'Некорректные входные данные.',
                'details': exc.errors(),
            },
        )

    @app.get('/health')
    def healthcheck():
        return {'status': 'ok'}

    return app


app = create_app()
