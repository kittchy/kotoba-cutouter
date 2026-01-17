"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import ensure_directories, get_settings

from src.routers import pages, transcription, video

# Global instances
settings = get_settings()
templates = Jinja2Templates(directory="src/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup: Create necessary directories
    ensure_directories(settings)

    # Create static directories if they don't exist
    Path("static/css").mkdir(parents=True, exist_ok=True)
    Path("static/js").mkdir(parents=True, exist_ok=True)

    # Load faster-whisper model at startup
    from src.services.transcription_service import TranscriptionService
    transcription_svc = TranscriptionService(
        model_size=settings.WHISPER_MODEL_SIZE,
        device=settings.WHISPER_DEVICE
    )
    transcription.set_transcription_service(transcription_svc)
    print(f"Loaded faster-whisper model: {settings.WHISPER_MODEL_SIZE}")

    yield

    # Shutdown: Cleanup if needed
    pass


# Create FastAPI application
app = FastAPI(
    title="kotoba-cutouter",
    description="Video trimming tool with word-level transcription search",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(pages.router)
app.include_router(video.router)
app.include_router(transcription.router)

# TODO: Include other routers (in Phase 4+)
# from src.routers import search
# app.include_router(search.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "kotoba-cutouter is running",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
