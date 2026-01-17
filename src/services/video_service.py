"""Video file operations service"""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

from src.config import get_settings
from src.models import VideoMetadata, VideoStatus
from src.services.storage_service import StorageService

settings = get_settings()


class VideoService:
    """Handle video file operations"""

    @staticmethod
    async def save_uploaded_file(file: UploadFile) -> VideoMetadata:
        """
        Save uploaded video file to storage

        Steps:
        1. Generate unique ID
        2. Validate file type and size
        3. Save to uploads/ directory
        4. Extract video metadata (duration, format)

        Args:
            file: Uploaded video file

        Returns:
            VideoMetadata object

        Raises:
            HTTPException: If file validation fails
        """
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイル名が不正です")

        # Check extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です。対応形式: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        # Generate unique ID and filename
        video_id = str(uuid.uuid4())
        filename = f"{video_id}{file_ext}"

        # Save file
        file_path = await StorageService.save_file(file, settings.UPLOAD_DIR, filename)

        # Check file size after saving
        file_size = StorageService.get_file_size(Path(file_path))
        if file_size > settings.MAX_FILE_SIZE:
            # Delete file if too large
            StorageService.delete_file(Path(file_path))
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが大きすぎます（最大{settings.MAX_FILE_SIZE // 1024 // 1024}MB）",
            )

        # Extract video metadata
        duration = VideoService.get_video_duration(file_path)

        # Create metadata object
        metadata = VideoMetadata(
            id=video_id,
            filename=file.filename,
            filepath=file_path,
            uploaded_at=datetime.now(),
            duration=duration,
            status=VideoStatus.UPLOADED,
        )

        return metadata

    @staticmethod
    def get_video_duration(video_path: str) -> Optional[float]:
        """
        Extract video duration using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds, or None if extraction fails
        """
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                video_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)

            # Extract duration from format
            if "format" in metadata and "duration" in metadata["format"]:
                return float(metadata["format"]["duration"])

            return None

        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
        ):
            return None

    @staticmethod
    def get_video_info(video_path: str) -> dict:
        """
        Extract detailed video metadata using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing video metadata
        """
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                video_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)

            # Extract relevant information
            video_info = {
                "duration": None,
                "width": None,
                "height": None,
                "codec": None,
                "format": None,
            }

            # Get format info
            if "format" in metadata:
                video_info["duration"] = metadata["format"].get("duration")
                video_info["format"] = metadata["format"].get("format_name")

            # Get video stream info
            if "streams" in metadata:
                for stream in metadata["streams"]:
                    if stream.get("codec_type") == "video":
                        video_info["width"] = stream.get("width")
                        video_info["height"] = stream.get("height")
                        video_info["codec"] = stream.get("codec_name")
                        break

            return video_info

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return {}

    @staticmethod
    async def trim_video(
        video_path: str, start_time: float, end_time: float, output_path: str
    ) -> str:
        """
        Trim video using ffmpeg

        Args:
            video_path: Input video path
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Output video path

        Returns:
            Path to trimmed video

        Raises:
            HTTPException: If ffmpeg command fails
        """
        try:
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-ss",
                str(start_time),
                "-to",
                str(end_time),
                "-c",
                "copy",  # Fast processing (no re-encoding)
                "-y",  # Overwrite output file
                output_path,
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            return output_path

        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"動画のトリミングに失敗しました: {e.stderr.decode() if e.stderr else 'Unknown error'}",
            )
