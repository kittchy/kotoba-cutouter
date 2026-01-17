"""Transcription endpoints"""

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse

from src.config import get_settings
from src.services.transcription_service import TranscriptionService

router = APIRouter()
settings = get_settings()

# Global transcription service instance (loaded at startup)
transcription_service: TranscriptionService | None = None


def set_transcription_service(service: TranscriptionService):
    """Set global transcription service instance"""
    global transcription_service
    transcription_service = service


@router.post("/transcribe/{video_id}", response_class=HTMLResponse)
async def start_transcription(video_id: str, background_tasks: BackgroundTasks):
    """
    Start transcription for uploaded video

    Args:
        video_id: Video ID
        background_tasks: FastAPI background tasks

    Returns:
        HTML fragment with transcription status
    """
    # Check if transcription service is loaded
    if transcription_service is None:
        return '<div class="error">文字起こしサービスが初期化されていません</div>'

    # Find video file
    video_path = None
    for ext in settings.ALLOWED_EXTENSIONS:
        candidate = settings.UPLOAD_DIR / f"{video_id}{ext}"
        if candidate.exists():
            video_path = str(candidate)
            break

    if not video_path:
        return '<div class="error">動画ファイルが見つかりません</div>'

    # Check if transcript already exists
    existing_transcript = TranscriptionService.load_transcript(video_id)
    if existing_transcript:
        # Transcript already exists, show search form
        return _render_search_form(video_id)

    # Start transcription in background
    background_tasks.add_task(_transcribe_task, video_id, video_path)

    # Return progress indicator with polling
    return f"""
    <div id="transcribe-result">
        <div
            hx-get="/transcribe/status/{video_id}"
            hx-trigger="every 2s"
            hx-target="this"
            hx-swap="outerHTML">
            <div class="success">
                <p>⏳ 文字起こし処理中...</p>
                <p>この処理には数分かかる場合があります。しばらくお待ちください。</p>
            </div>
        </div>
    </div>
    """


@router.get("/transcribe/status/{video_id}", response_class=HTMLResponse)
async def check_transcription_status(video_id: str):
    """
    Check transcription status

    Args:
        video_id: Video ID

    Returns:
        HTML fragment with current status
    """
    # Check if transcript exists
    transcript = TranscriptionService.load_transcript(video_id)

    if transcript:
        # Transcription complete
        return _render_search_form(video_id)
    else:
        # Still processing
        return """
        <div
            hx-get="/transcribe/status/{}"
            hx-trigger="every 2s"
            hx-target="this"
            hx-swap="outerHTML">
            <div class="success">
                <p>⏳ 文字起こし処理中...</p>
                <p>この処理には数分かかる場合があります。しばらくお待ちください。</p>
            </div>
        </div>
        """.format(video_id)


def _render_search_form(video_id: str) -> str:
    """Render search form HTML"""
    return f"""
    <div class="success">
        <p>✅ 文字起こしが完了しました！</p>
    </div>
    <div id="search-container">
        <form
            hx-post="/search"
            hx-trigger="keyup changed delay:500ms from:#keyword"
            hx-target="#search-results"
            hx-include="[name='video_id']">
            <input type="hidden" name="video_id" value="{video_id}">
            <div class="form-group">
                <label for="keyword">検索する単語・フレーズを入力してください</label>
                <input
                    type="text"
                    id="keyword"
                    name="keyword"
                    placeholder="例: こんにちは"
                    autocomplete="off">
            </div>
        </form>
        <div id="search-results"></div>
    </div>
    <script>
        // Show search section
        document.getElementById('search-section').style.display = 'block';
    </script>
    """


async def _transcribe_task(video_id: str, video_path: str):
    """
    Background task for transcription

    Args:
        video_id: Video ID
        video_path: Path to video file
    """
    if transcription_service is None:
        raise RuntimeError("Transcription service is not initialized")

    try:
        await transcription_service.transcribe_video(
            video_id=video_id, video_path=video_path, language="ja"
        )
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Transcription error: {e}")
