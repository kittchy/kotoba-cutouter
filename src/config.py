"""Application configuration settings"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # File storage directories
    UPLOAD_DIR: Path = Path("uploads")
    OUTPUT_DIR: Path = Path("outputs")
    TRANSCRIPT_DIR: Path = Path("transcripts")
    TEMP_DIR: Path = Path("temp")

    # File size limits
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB

    # Whisper model settings
    WHISPER_MODEL_SIZE: Literal[
        "tiny", "base", "small", "medium", "large", "large-v3"
    ] = "base"
    WHISPER_DEVICE: Literal["cpu", "cuda"] = "cpu"

    # Allowed video file extensions
    ALLOWED_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    # Cleanup settings
    MAX_FILE_AGE_HOURS: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()


def ensure_directories(settings: Settings) -> None:
    """Create necessary directories if they don't exist"""
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
