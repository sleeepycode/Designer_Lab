import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.document_api import router as document_router
from app.core.config import settings, ensure_dirs

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [DOC_SERVICE] %(message)s',
    datefmt='%H:%M:%S',
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    ensure_dirs()

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version='1.0.0',
        description='Microservice for document processing with GOST formatting'
    )

    @app.on_event('startup')
    async def startup_event():
        logger.info('Doc Service startup')
        logger.info('SERVICE_URL=%s', settings.service_url)
        logger.info('ML_SERVICE_URL=%s', settings.ml_service_url)
        logger.info('STORAGE_DIR=%s', settings.storage_dir)
        logger.info('Swagger UI: /docs')

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

    @app.get('/')
    def healthcheck():
        return {'status': 'ok', 'service': 'doc-service'}

    storage_path = Path(settings.storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount('/storage', StaticFiles(directory=str(storage_path)), name='storage')
    logger.info('Mounted static storage at /storage -> %s', storage_path.resolve())

    app.include_router(document_router)

    return app


app = create_app()
