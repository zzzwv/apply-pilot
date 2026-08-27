from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.database import check_database, engine
from app.core.errors import AppError, ErrorCode
from app.core.handlers import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import request_id_middleware
from app.core.redis import check_redis, close_redis
from app.core.responses import success_response

HealthCheck = Callable[[], Awaitable[None]]


async def check_dependencies() -> None:
    await check_database()
    await check_redis()


def create_app(health_check: HealthCheck | None = None) -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await close_redis()
        await engine.dispose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.middleware("http")(request_id_middleware)
    install_exception_handlers(app)
    app.include_router(api_router)
    readiness_check = health_check or check_dependencies

    @app.get("/health")
    async def health():
        try:
            await readiness_check()
        except Exception as exc:
            raise AppError(ErrorCode.SERVICE_UNAVAILABLE, "Service unavailable") from exc
        return success_response({"status": "ok"})

    return app


app = create_app()
