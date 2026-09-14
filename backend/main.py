"""
Module   : App Entrypoint
Owner    : Backend Lead
Purpose  : FastAPI app initialization, router registration, startup/shutdown events.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from config import settings
from dependencies import preload_tts_prompts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        n = preload_tts_prompts()
        print(f"[startup] Preloaded {n} common TTS prompts")
    except Exception as exc:
        print(f"[startup] TTS preload failed (non-fatal): {exc}")
    yield
    # Shutdown - nothing special for in-memory services


def create_app() -> FastAPI:
    app = FastAPI(
        title="MediKiosk — Patient Case-Taking Software",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS - allow all for hackathon/demo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler (basic)
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return {"detail": "Internal server error"}, 500

    # Mount API routers
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.env == "development",
        log_level=settings.log_level,
    )