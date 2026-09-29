"""
Module   : App Entrypoint
Owner    : Backend Lead
Purpose  : FastAPI app initialization, router registration, startup/shutdown events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import api_router
from backend.config import settings
from backend.dependencies import preload_tts_prompts
from backend.utils.logger import clear_request_id, get_logger, set_request_id

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        n = preload_tts_prompts()
        logger.info("startup", extra={"extra_fields": {"tts_prompts_preloaded": n}})
    except Exception as exc:
        logger.error("startup_failed", extra={"extra_fields": {"error": str(exc)}})
    yield
    # Shutdown
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Curo — Patient Case-Taking Software",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS - configurable origins
    allowed_origins = settings.cors_origins if hasattr(settings, "cors_origins") and settings.cors_origins else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or set_request_id()
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        clear_request_id()
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "unhandled_exception",
            extra={"extra_fields": {"path": request.url.path, "method": request.method}},
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Mount API routers
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "development",
        log_level=settings.log_level,
    )
