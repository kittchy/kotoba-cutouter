"""Video upload and processing endpoints"""

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services.video_service import VideoService

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


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

        # Return HTML fragment with video info
        return f"""
        <div class="success">
            <p>✅ アップロード完了！</p>
            <p>ファイル名: {metadata.filename}</p>
            <p>動画の長さ: {duration_str}</p>
        </div>
        <div id="transcribe-container">
            <button
                class="primary"
                hx-post="/transcribe/{metadata.id}"
                hx-target="#transcribe-result"
                hx-indicator="#transcribe-spinner">
                文字起こしを開始
            </button>
            <span id="transcribe-spinner" class="htmx-indicator">
                <span class="spinner"></span> 処理中...
            </span>
            <div id="transcribe-result"></div>
        </div>
        """

    except HTTPException as e:
        return f'<div class="error">{e.detail}</div>'
    except Exception as e:
        return f'<div class="error">アップロードに失敗しました: {str(e)}</div>'
