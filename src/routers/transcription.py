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
        return '''<div class="error htmx-added">
            <h3 style="margin: 0 0 0.5rem 0;">❌ サービスエラー</h3>
            <p style="margin: 0;">文字起こしサービスが初期化されていません</p>
        </div>'''

    # Find video file
    video_path = None
    for ext in settings.ALLOWED_EXTENSIONS:
        candidate = settings.UPLOAD_DIR / f"{video_id}{ext}"
        if candidate.exists():
            video_path = str(candidate)
            break

    if not video_path:
        return '''<div class="error htmx-added">
            <h3 style="margin: 0 0 0.5rem 0;">❌ ファイルが見つかりません</h3>
            <p style="margin: 0;">動画ファイルが見つかりません。再度アップロードしてください。</p>
        </div>'''

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
            hx-swap="outerHTML swap:300ms">
            <div class="info htmx-added">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <div class="spinner" style="width: 30px; height: 30px;"></div>
                    <div>
                        <h3 style="margin: 0;">⏳ 文字起こし処理中...</h3>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">faster-whisper で音声を解析しています</p>
                    </div>
                </div>
                <div class="progress">
                    <div class="progress-bar pulse" style="width: 100%;">処理中...</div>
                </div>
                <p style="margin-top: 1rem; font-size: 0.9rem;">
                    💡 ヒント: この処理には数分かかる場合があります。動画の長さに応じて時間がかかります。
                </p>
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
            hx-swap="outerHTML swap:300ms">
            <div class="info htmx-added">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <div class="spinner" style="width: 30px; height: 30px;"></div>
                    <div>
                        <h3 style="margin: 0;">⏳ 文字起こし処理中...</h3>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">faster-whisper で音声を解析しています</p>
                    </div>
                </div>
                <div class="progress">
                    <div class="progress-bar pulse" style="width: 100%;">処理中...</div>
                </div>
                <p style="margin-top: 1rem; font-size: 0.9rem;">
                    💡 ヒント: この処理には数分かかる場合があります。動画の長さに応じて時間がかかります。
                </p>
            </div>
        </div>
        """.format(video_id)


def _render_search_form(video_id: str) -> str:
    """Render search form HTML"""
    return f"""
    <div class="success htmx-added">
        <h3 style="margin: 0 0 0.5rem 0;">✅ 文字起こしが完了しました！</h3>
        <p style="margin: 0;">単語レベルのタイムスタンプ付きで文字起こしが完了しました。検索を開始できます。</p>
    </div>
    <div id="search-container" hx-swap-oob="innerHTML">
        <form
            hx-post="/search"
            hx-trigger="keyup changed delay:500ms from:#keyword"
            hx-target="#search-results"
            hx-swap="innerHTML swap:300ms"
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
        // Show search section with animation
        const searchSection = document.getElementById('search-section');
        searchSection.style.display = 'block';
        searchSection.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
    </script>
    """.replace("{{", "{").replace("}}", "}")


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
