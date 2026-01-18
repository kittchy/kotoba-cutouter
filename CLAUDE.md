# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

kotoba-cutouter（コトバ・カットアウター）は、動画から特定の単語が発言された区間を自動検知し、その部分を切り抜くWebアプリケーションです。faster-whisperによる**word-level timestamp**を使用した高精度な音声認識が特徴です。

## 開発コマンド

### 依存関係のインストール
```bash
uv sync
```

### 開発サーバーの起動（ホットリロード）
```bash
uvicorn src.main:app --reload
```

### Docker環境（推奨）
```bash
# 通常モード
docker-compose up

# 開発モード（ホットリロード）
docker-compose --profile dev up app-dev
```

### テスト実行
```bash
pytest tests/
```

### コードフォーマットとリント
```bash
# フォーマット
ruff format src/

# リントチェック
ruff check src/
```

## 技術スタック

- **バックエンド**: FastAPI + Pydantic + uvicorn
- **音声認識**: faster-whisper（word-level timestamp対応）
- **フロントエンド**: HTMX + Jinja2（サーバーサイドレンダリング）
- **動画処理**: FFmpeg（subprocess経由で直接実行）

## アーキテクチャの重要なポイント

### 1. word-level timestampの利用

このアプリの最大の特徴は、**単語レベルの正確なタイムスタンプ**を使用した切り抜き機能です：

- `TranscriptionService`は`word_timestamps=True`でfaster-whisperを実行
- 各単語に`start`/`end`/`probability`を含む`WordTimestamp`が生成される
- 検索時は`word.word`フィールドでマッチングし、単語単位の正確な切り抜きを実現

```python
# 文字起こし実行時
segments, info = model.transcribe(
    audio_file,
    language="ja",
    word_timestamps=True  # 必須：単語レベルのタイムスタンプを有効化
)

# 検索時
for segment in transcript.segments:
    for word in segment.words:
        if keyword.lower() in word.word.lower():
            # word.start, word.end が正確なタイムスタンプ
```

### 2. レイヤー構造

```
Presentation Layer (HTMX + Jinja2)
    ↓
API Layer (FastAPI Routers)
    ↓ src/routers/
    ├── pages.py        - ページ表示
    ├── video.py        - 動画アップロード
    ├── transcription.py - 文字起こし
    └── search.py       - 検索と切り抜き
    ↓
Business Logic Layer (Services)
    ↓ src/services/
    ├── video_service.py         - 動画処理（FFmpeg）
    ├── transcription_service.py - 音声認識（faster-whisper）
    └── storage_service.py       - ファイル管理
    ↓
Infrastructure Layer
    ├── faster-whisper (AIモデル)
    ├── ffmpeg (動画/音声処理)
    └── File System (uploads/, outputs/, transcripts/, temp/)
```

### 3. データフロー

1. **アップロード**: `video.py` → `VideoService.save_uploaded_file()` → `uploads/`
2. **文字起こし**: `transcription.py` → `TranscriptionService.transcribe_video()` → word-level timestampを含むJSON → `transcripts/`
3. **検索**: `search.py` → `transcript.segments[].words[]`を検索 → word-level matchを返す
4. **切り抜き**: `search.py` → `VideoService.trim_video()` → FFmpegで`-ss`/`-to`/`-c copy`実行 → `temp/` → ストリーミングレスポンス → 自動削除

### 4. FFmpegの直接実行

このプロジェクトでは、ライブラリではなく**subprocessでFFmpegコマンドを直接実行**しています：

```python
# 音声抽出（transcription_service.py:127-140）
cmd = ["ffmpeg", "-i", video_path, "-ar", "16000", "-ac", "1", "-vn", "-y", audio_path]
subprocess.run(cmd, check=True, capture_output=True)

# 動画トリミング（video_service.py:199-213）
cmd = ["ffmpeg", "-i", video_path, "-ss", str(start), "-to", str(end), "-c", "copy", "-y", output_path]
subprocess.run(cmd, check=True, capture_output=True)
```

### 5. モデルの起動時ロード

faster-whisperモデルは`main.py`の`lifespan`イベントで一度だけロードされます（src/main.py:18-39）。これにより初回リクエストの遅延を防ぎます。

### 6. HTMXによるインタラクティブUI

- フォーム送信: `hx-post="/upload"` + `hx-target="#result"`
- リアルタイム検索: `hx-trigger="keyup changed delay:500ms"`
- ポーリング: `hx-get="/status/{id}"` + `hx-trigger="every 2s"`
- ストリーミングダウンロード: `FileResponse`で一時ファイルを返し、自動クリーンアップ

## データモデル（src/models.py）

重要なモデル：

- `VideoMetadata`: 動画のメタデータ（id, filename, filepath, duration, status）
- `WordTimestamp`: **単語レベルのタイムスタンプ**（word, start, end, probability）
- `TranscriptSegment`: セグメント + `words: list[WordTimestamp]`
- `Transcript`: 完全な文字起こし結果（video_id, segments, language）
- `WordMatch`: 検索結果（word, start, end, context, segment_index）

## 設定（src/config.py）

環境変数で変更可能：

- `WHISPER_MODEL_SIZE`: tiny/base/small/medium/large（デフォルト: base）
- `WHISPER_DEVICE`: cpu/cuda（デフォルト: cpu）
- `MAX_FILE_SIZE`: 最大ファイルサイズ（デフォルト: 500MB）
- `UPLOAD_DIR`, `OUTPUT_DIR`, `TRANSCRIPT_DIR`, `TEMP_DIR`: ディレクトリパス

## 開発時の注意点

1. **文字コード**: 全てのファイルはUTF-8で保存すること（SHIFT-JISは文字化けの原因）
2. **FFmpeg必須**: システムにFFmpegがインストールされている必要がある
3. **一時ファイル**: `temp/`ディレクトリの一時ファイルは自動削除される
4. **word-level timestamp**: 検索機能を実装する際は必ず`segment.words`を使用すること
5. **非同期処理**: 文字起こしは時間がかかるため、`BackgroundTasks`またはポーリングを使用
6. **ストリーミング**: 切り抜いた動画は`FileResponse`で直接返し、`outputs/`には保存しない

## トラブルシューティング

- **FFmpeg not found**: `brew install ffmpeg`（macOS）または`apt install ffmpeg`（Ubuntu）
- **Out of memory**: より小さいモデル（tiny/base）を使用
- **文字起こしが遅い**: GPU対応の場合は`WHISPER_DEVICE=cuda`に設定
- **文字化け**: ファイルがUTF-8で保存されているか確認

## 参考ドキュメント

詳細な設計とアーキテクチャについては以下を参照：

- [docs/design.md](docs/design.md) - システム設計、機能要件、実装計画
- [docs/architecture.md](docs/architecture.md) - アーキテクチャ詳細、データフロー、実装パターン
