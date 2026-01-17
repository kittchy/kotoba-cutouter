# kotoba-cutouter アーキテクチャ詳細

## 1. システムアーキテクチャ

### 1.1 レイヤー構造

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│              (HTMX + Jinja2 Templates)                   │
│  - User Interface                                        │
│  - HTML Fragments                                        │
│  - Client-side interactions                              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    API Layer                             │
│                   (FastAPI Routers)                      │
│  - Request validation                                    │
│  - Response formatting                                   │
│  - Error handling                                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Business Logic Layer                    │
│                   (Services)                             │
│  - VideoService: Upload, trim, storage                   │
│  - TranscriptionService: Audio extraction, transcribe    │
│  - SearchService: Keyword matching, timestamp extraction │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                Infrastructure Layer                      │
│  - faster-whisper: AI model                             │
│  - ffmpeg: Video/audio processing                       │
│  - File System: Storage                                 │
└─────────────────────────────────────────────────────────┘
```

## 2. コンポーネント詳細

### 2.1 VideoService

**責務**: 動画ファイルの管理と処理

```python
class VideoService:
    """Handle video file operations"""

    async def save_uploaded_file(file: UploadFile) -> VideoMetadata:
        """
        Save uploaded video file to storage
        - Generate unique ID
        - Validate file type and size
        - Save to uploads/ directory
        - Extract video metadata (duration, format)
        """
        pass

    async def trim_video(
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """
        Trim video using ffmpeg (subprocess)
        - Execute ffmpeg command directly via subprocess
        - Use -c copy for fast processing (no re-encoding)
        - Return path to trimmed video

        Example:
            import subprocess

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_time),
                '-to', str(end_time),
                '-c', 'copy',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        """
        pass

    def get_video_info(video_path: str) -> VideoMetadata:
        """
        Extract video metadata using ffprobe (subprocess)
        - Duration
        - Resolution
        - Format
        - Codec

        Example:
            import subprocess
            import json

            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            metadata = json.loads(result.stdout)
        """
        pass
```

### 2.2 TranscriptionService

**責務**: 音声認識と文字起こし（word-level timestampサポート）

```python
class TranscriptionService:
    """Handle audio transcription using faster-whisper with word-level timestamps"""

    def __init__(self, model_size: str = "base"):
        """
        Initialize faster-whisper model
        - Load model once at startup
        - Support models: tiny, base, small, medium, large
        - Device: cpu or cuda
        """
        self.model = WhisperModel(model_size, device="cpu")

    async def transcribe_video(
        video_path: str,
        language: str = "ja"
    ) -> Transcript:
        """
        Transcribe video audio to text with word-level timestamps
        1. Extract audio from video (ffmpeg)
        2. Run faster-whisper transcription with word_timestamps=True
        3. Generate transcript with word-level timestamps
        4. Save transcript as JSON

        Example:
            segments, info = model.transcribe(
                audio_file,
                language="ja",
                word_timestamps=True  # Enable word-level timestamps
            )

            for segment in segments:
                for word in segment.words:
                    print(f"{word.word}: {word.start} - {word.end}")
        """
        pass

    def extract_audio(video_path: str) -> str:
        """
        Extract audio track from video using ffmpeg (subprocess)
        - Convert to WAV format (whisper compatible)
        - 16kHz sample rate recommended
        - Return path to audio file

        Example:
            import subprocess

            audio_path = f"{video_id}.wav"
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # mono
                '-vn',           # no video
                audio_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return audio_path
        """
        pass
```

### 2.3 SearchService

**責務**: トランスクリプト内の単語検索（word-level timestamp対応）

```python
class SearchService:
    """Handle keyword search in transcripts using word-level timestamps"""

    def search_keyword(
        transcript: Transcript,
        keyword: str,
        context_padding: float = 2.0
    ) -> SearchResult:
        """
        Search for keyword in transcript using word-level timestamps
        - Search through word-level timestamps for exact matches
        - Case-insensitive matching
        - Return all matching words with their exact timestamps
        - Add padding for context (before/after)
        - Support fuzzy matching (optional)

        Example:
            # Search for "こんにちは" in word-level timestamps
            matches = []
            for segment in transcript.segments:
                for word in segment.words:
                    if keyword.lower() in word.word.lower():
                        matches.append({
                            'word': word.word,
                            'start': word.start - context_padding,
                            'end': word.end + context_padding
                        })
        """
        pass

    def search_phrase(
        transcript: Transcript,
        phrase: str,
        context_padding: float = 2.0
    ) -> SearchResult:
        """
        Search for multi-word phrase in transcript
        - Match consecutive words that form the phrase
        - Return start time of first word, end time of last word
        - Add context padding
        """
        pass

    def extract_timestamps(
        matches: List[SearchMatch]
    ) -> List[Tuple[float, float]]:
        """
        Extract start/end timestamps from matches
        - Use word-level timestamps for precise trimming
        - Merge overlapping segments
        - Add context padding
        - Return list of (start, end) tuples
        """
        pass
```

### 2.4 StorageService

**責務**: ファイルシステム管理

```python
class StorageService:
    """Manage file storage and cleanup"""

    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TRANSCRIPT_DIR = "transcripts"

    def save_file(file: UploadFile, directory: str) -> str:
        """Save uploaded file and return path"""
        pass

    def cleanup_old_files(max_age_hours: int = 24):
        """
        Remove old files to prevent storage overflow
        - Delete files older than max_age_hours
        - Run as background task
        """
        pass

    def get_file_size(path: str) -> int:
        """Get file size in bytes"""
        pass
```

## 3. データフロー詳細

### 3.1 動画アップロードフロー

```
┌──────┐
│ User │
└──┬───┘
   │ 1. Select video file
   ▼
┌──────────────┐
│ Upload Form  │ (HTMX)
└──┬───────────┘
   │ 2. POST /upload (multipart/form-data)
   ▼
┌──────────────────┐
│ FastAPI Router   │
│ video.py         │
└──┬───────────────┘
   │ 3. Validate file
   ▼
┌──────────────────┐
│ VideoService     │
└──┬───────────────┘
   │ 4. Save to uploads/
   │ 5. Generate UUID
   │ 6. Extract metadata
   ▼
┌──────────────────┐
│ File System      │
│ uploads/         │
│ ├── {uuid}.mp4  │
└──────────────────┘
   │
   ▼
┌──────────────────┐
│ Response         │ HTML fragment with video info
│ (HTMX swap)      │ and "Transcribe" button
└──────────────────┘
```

### 3.2 文字起こしフロー

```
┌──────┐
│ User │ Click "Transcribe"
└──┬───┘
   │ 1. POST /transcribe/{video_id}
   ▼
┌──────────────────┐
│ FastAPI Router   │
└──┬───────────────┘
   │ 2. Start background task
   ▼
┌────────────────────────┐
│ TranscriptionService   │
└──┬─────────────────────┘
   │ 3. Extract audio
   ▼
┌──────────────────┐
│ ffmpeg           │ Extract audio → temp.wav
└──┬───────────────┘
   │ 4. Audio file
   ▼
┌──────────────────┐
│ faster-whisper   │
│ (word_timestamps │
│  =True)          │
└──┬───────────────┘
   │ 5. Transcribe with word-level timestamps
   ▼
┌──────────────────┐
│ Transcript       │
│ {                │
│   segments: [    │
│     {            │
│       start: 0.0 │
│       end: 2.5   │
│       text: "..." │
│       words: [   │
│         {        │
│           word: "こんにちは" │
│           start: 0.0        │
│           end: 1.2          │
│         }        │
│       ]          │
│     }            │
│   ]              │
│ }                │
└──┬───────────────┘
   │ 6. Save as JSON
   ▼
┌──────────────────┐
│ transcripts/     │
│ {uuid}.json      │
└──────────────────┘
   │
   ▼
┌──────────────────┐
│ Response         │ HTML fragment with transcript
│ (HTMX)           │ and search form
└──────────────────┘
```

### 3.3 検索と切り抜きフロー (word-level timestamp対応)

```
┌──────┐
│ User │ Enter keyword "こんにちは"
└──┬───┘
   │ 1. POST /search
   ▼
┌──────────────────┐
│ SearchService    │
└──┬───────────────┘
   │ 2. Load transcript JSON with word-level timestamps
   │ 3. Search keyword in word.word fields
   ▼
┌──────────────────┐
│ Word Matches     │
│ [                │
│   {              │
│     word: "こんにちは" │
│     start: 15.2  │  ← Word-level precision!
│     end: 16.5    │
│     context: "..." │
│   },             │
│   ...            │
│ ]                │
└──┬───────────────┘
   │ 4. Display word matches with context
   ▼
┌──────────────────┐
│ User selects     │ Click "Download this clip"
│ word match       │
└──┬───────────────┘
   │ 5. POST /trim (with context padding)
   ▼
┌──────────────────┐
│ VideoService     │
└──┬───────────────┘
   │ 6. Trim video with ffmpeg to temp file
   ▼
┌──────────────────┐
│ ffmpeg           │
│ -i input.mp4     │
│ -ss 13.2         │  ← start - padding
│ -to 18.5         │  ← end + padding
│ -c copy          │
│ temp_{uuid}.mp4  │
└──┬───────────────┘
   │ 7. Stream temp file as response
   ▼
┌──────────────────┐
│ FileResponse     │
│ (streaming)      │
└──┬───────────────┘
   │ 8. After streaming complete, delete temp file
   ▼
┌──────────────────┐
│ Cleanup          │ Delete temp/{uuid}.mp4
│                  │
└──────────────────┘
```

## 4. HTMX統合パターン

### 4.1 ファイルアップロード

```html
<!-- Upload form -->
<form
    hx-post="/upload"
    hx-encoding="multipart/form-data"
    hx-target="#upload-result"
    hx-indicator="#upload-spinner">
    <input type="file" name="video" accept="video/*" required>
    <button type="submit">Upload</button>
    <span id="upload-spinner" class="htmx-indicator">Uploading...</span>
</form>

<!-- Result container -->
<div id="upload-result"></div>
```

**サーバーレスポンス**:
```html
<div>
    <p>Video uploaded: example.mp4 (5.2 MB)</p>
    <button
        hx-post="/transcribe/abc-123-def"
        hx-target="#transcribe-result"
        hx-indicator="#transcribe-spinner">
        Start Transcription
    </button>
    <span id="transcribe-spinner" class="htmx-indicator">Processing...</span>
</div>
```

### 4.2 進捗ポーリング

```html
<div
    hx-get="/status/task-123"
    hx-trigger="every 2s"
    hx-target="this"
    hx-swap="outerHTML">
    <div>Processing... 45%</div>
    <progress value="45" max="100"></progress>
</div>
```

**完了時のレスポンス**:
```html
<div>
    <p>✅ Transcription complete!</p>
    <div id="search-form">
        <!-- Search form here -->
    </div>
</div>
```

### 4.3 リアルタイム検索

```html
<input
    type="text"
    name="keyword"
    hx-post="/search"
    hx-trigger="keyup changed delay:500ms"
    hx-target="#search-results"
    hx-include="[name='video_id']"
    placeholder="Search keyword...">

<input type="hidden" name="video_id" value="abc-123">

<div id="search-results">
    <!-- Results will appear here -->
</div>
```

## 5. エラーハンドリング

### 5.1 FastAPI例外ハンドラ

```python
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return HTMX-friendly error messages"""
    return HTMLResponse(
        content=f'<div class="error">{exc.detail}</div>',
        status_code=exc.status_code
    )
```

### 5.2 エラーケース

| Error | HTTP Status | Message | Action |
|-------|-------------|---------|--------|
| File too large | 413 | ファイルサイズが大きすぎます（最大500MB） | Show error in UI |
| Invalid file type | 400 | 動画ファイルのみアップロード可能です | Show error in UI |
| Transcription failed | 500 | 文字起こしに失敗しました | Retry button |
| Video not found | 404 | 動画が見つかりません | Redirect to home |
| FFmpeg error | 500 | 動画処理に失敗しました | Show error details |

## 6. パフォーマンス最適化

### 6.1 モデルの事前ロード

```python
# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load whisper model
    global transcription_service
    transcription_service = TranscriptionService(model_size="base")
    yield
    # Shutdown: Cleanup
    pass

app = FastAPI(lifespan=lifespan)
```

### 6.2 バックグラウンドタスク

```python
from fastapi import BackgroundTasks

@app.post("/transcribe/{video_id}")
async def start_transcription(
    video_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        transcription_service.transcribe_video,
        video_id
    )
    return HTMLResponse("Transcription started...")
```

### 6.3 ファイルストリーミング

```python
from fastapi.responses import FileResponse

@app.get("/download/{output_id}")
async def download_video(output_id: str):
    file_path = f"outputs/{output_id}.mp4"
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=f"trimmed_{output_id}.mp4"
    )
```

## 7. セキュリティ対策

### 7.1 ファイルバリデーション

```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

async def validate_video_file(file: UploadFile):
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    # Check size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset

    if size > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large")

    return True
```

### 7.2 パス サニタイズ

```python
import uuid
from pathlib import Path

def safe_filename(filename: str) -> str:
    """Generate safe filename using UUID"""
    ext = Path(filename).suffix
    return f"{uuid.uuid4()}{ext}"
```

### 7.3 ファイル自動削除

```python
from datetime import datetime, timedelta

async def cleanup_old_files():
    """Remove files older than 24 hours"""
    max_age = datetime.now() - timedelta(hours=24)

    for directory in ["uploads", "outputs", "transcripts"]:
        for file_path in Path(directory).glob("*"):
            if file_path.stat().st_mtime < max_age.timestamp():
                file_path.unlink()
```

## 8. テスト戦略

### 8.1 ユニットテスト

```python
# tests/test_video_service.py
def test_trim_video():
    service = VideoService()
    result = service.trim_video(
        "test_video.mp4",
        start_time=10.0,
        end_time=20.0,
        output_path="output.mp4"
    )
    assert os.path.exists(result)
    assert get_video_duration(result) == pytest.approx(10.0, rel=0.1)
```

### 8.2 統合テスト

```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_upload_endpoint():
    client = TestClient(app)
    with open("test_video.mp4", "rb") as f:
        response = client.post(
            "/upload",
            files={"video": ("test.mp4", f, "video/mp4")}
        )
    assert response.status_code == 200
    assert "Video uploaded" in response.text
```

## 9. デプロイメント

### 9.1 開発環境

```bash
# Install dependencies
uv sync

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 9.2 本番環境（例）

```bash
# Using uvicorn with workers
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 9.3 環境変数

```env
# .env
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
TRANSCRIPT_DIR=transcripts
MAX_FILE_SIZE=524288000  # 500MB
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
```

## 10. 今後の拡張

### 10.1 短期的な改善

- [ ] 複数単語の同時検索
- [ ] 正規表現サポート
- [ ] 文字起こし結果のダウンロード（JSON/SRT形式）
- [ ] プレビュー機能（切り抜き前に確認）

### 10.2 中長期的な機能

- [ ] ユーザー認証とセッション管理
- [ ] 処理履歴の保存
- [ ] 複数言語サポート
- [ ] GPU対応（faster-whisper）
- [ ] WebSocketでのリアルタイム進捗
- [ ] クラウドストレージ統合（S3）
- [ ] Celeryでのタスクキュー
- [ ] Docker化

