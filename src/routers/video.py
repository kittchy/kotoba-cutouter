"""Video upload and processing endpoints"""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config import get_settings
from src.services.video_service import VideoService

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")
settings = get_settings()


@router.post("/upload", response_class=HTMLResponse)
async def upload_video(video: UploadFile = File(...)):
    """
    Upload video file

    Args:
        video: Uploaded video file

    Returns:
        HTML fragment with upload result
    """
    try:
        # Save uploaded file and extract metadata
        metadata = await VideoService.save_uploaded_file(video)

        # Format duration
        duration_str = f"{metadata.duration:.1f}秒" if metadata.duration else "不明"

        # Return HTML fragment with video info only
        return f"""
        <div class="success htmx-added">
            <h3 style="margin: 0 0 0.5rem 0;">✅ アップロード完了！</h3>
            <p style="margin: 0.25rem 0;"><strong>ファイル名:</strong> {metadata.filename}</p>
            <p style="margin: 0.25rem 0;"><strong>動画の長さ:</strong> {duration_str}</p>
        </div>
        <div id="transcribe-container" hx-swap-oob="innerHTML">
            <button
                class="primary"
                hx-post="/transcribe/{metadata.id}"
                hx-target="#transcribe-result"
                hx-swap="innerHTML swap:300ms"
                hx-indicator="#transcribe-spinner">
                文字起こしを開始
            </button>
            <span id="transcribe-spinner" class="htmx-indicator">
                <span class="spinner"></span> 処理中...
            </span>
            <div id="transcribe-result"></div>
        </div>
        <script>
            // Show transcription section
            document.getElementById('transcription-section').style.display = 'block';
        </script>
        """

    except HTTPException as e:
        return f"""<div class="error htmx-added">
            <h3 style="margin: 0 0 0.5rem 0;">❌ エラーが発生しました</h3>
            <p style="margin: 0;">{e.detail}</p>
        </div>"""
    except Exception as e:
        return f"""<div class="error htmx-added">
            <h3 style="margin: 0 0 0.5rem 0;">❌ アップロードに失敗しました</h3>
            <p style="margin: 0;">{str(e)}</p>
        </div>"""


@router.post("/trim")
async def trim_video(
    background_tasks: BackgroundTasks,
    video_id: str = Form(...),
    start_time: float = Form(...),
    end_time: float = Form(...),
):
    """
    Trim video and return as streaming response

    Args:
        background_tasks: FastAPI background tasks for cleanup
        video_id: Video ID
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        FileResponse with trimmed video (streaming)
    """
    # Find source video file
    video_path = None
    video_ext = None
    for ext in settings.ALLOWED_EXTENSIONS:
        candidate = settings.UPLOAD_DIR / f"{video_id}{ext}"
        if candidate.exists():
            video_path = str(candidate)
            video_ext = ext
            break

    if not video_path:
        raise HTTPException(status_code=404, detail="Video not found")

    # Validate time range
    if start_time < 0:
        start_time = 0
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="Invalid time range")

    # Generate unique output filename in temp directory
    output_id = str(uuid.uuid4())
    output_filename = f"trimmed_{output_id}{video_ext}"
    output_path = str(settings.TEMP_DIR / output_filename)

    # Ensure temp directory exists
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Trim video using ffmpeg
    await VideoService.trim_video(
        video_path=video_path,
        start_time=start_time,
        end_time=end_time,
        output_path=output_path,
    )

    # Schedule cleanup of temp file after response is sent
    background_tasks.add_task(_cleanup_temp_file, output_path)

    # Return file as streaming response
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"clip_{video_id}_{int(start_time)}_{int(end_time)}{video_ext}",
    )


def _cleanup_temp_file(file_path: str):
    """
    Clean up temporary file after response is sent

    Args:
        file_path: Path to temporary file
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception:
        # Log error in production
        pass
