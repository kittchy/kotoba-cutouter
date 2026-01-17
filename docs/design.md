# kotoba-cutouter システム設計書

## 1. システム概要

kotoba-cutouter は、動画から特定の単語が発言された区間を自動検知し、その部分を切り抜くWebアプリケーションです。faster-whisperを使用した高速な音声認識と、FastAPI + HTMXによる軽量なWebインターフェースを特徴とします。

### 1.1 主な機能

- 動画ファイルのアップロード（MP4, MOV, AVI等）
- **faster-whisperによる音声の自動文字起こし（word-level timestamp対応）**
- **任意の単語・フレーズの検索（単語レベルの高精度検索）**
- 該当区間の自動検出とタイムスタンプ表示
- 検出された区間の動画切り抜き
- **切り抜いた動画の即座ダウンロード（ストリーミングレスポンス）**

### 1.2 word-level timestampの利点

このシステムは、faster-whisperの `word_timestamps=True` オプションを使用して、単語レベルの正確なタイムスタンプを取得します。

**従来の方法との比較：**

| 方式 | 精度 | 説明 |
|------|------|------|
| Segment-level | 低い | セグメント（文）全体のタイムスタンプのみ<br>例: "こんにちは、今日はいい天気ですね" → 0.0-5.0秒 |
| **Word-level** | **高い** | **各単語の正確なタイムスタンプ**<br>**例: "こんにちは" → 0.0-1.2秒, "今日は" → 1.3-2.1秒** |

**メリット：**

- ✅ 任意の単語を**ピンポイント**で切り出せる
- ✅ 不要な前後の発言を含まない
- ✅ 複数の単語が含まれる長いセグメントでも、特定の単語だけを抽出可能
- ✅ より自然な切り抜き動画（前後にコンテキストパディング追加可能）

## 2. 技術スタック

### 2.1 バックエンド

- **FastAPI**: 高速なPython Webフレームワーク
- **faster-whisper**: 音声認識エンジン（OpenAI Whisperの高速化版）
- **FFmpeg**: 動画処理（subprocessで直接実行）
- **python-multipart**: ファイルアップロード処理

### 2.2 フロントエンド

- **HTMX**: サーバーサイドレンダリングとインタラクティブUI
- **Jinja2**: HTMLテンプレートエンジン
- **TailwindCSS** (optional): CSSフレームワーク

### 2.3 その他

- **uvicorn**: ASGIサーバー
- **pydantic**: データバリデーション

## 3. アーキテクチャ

### 3.1 システム構成図

```
┌──────────────────────────────────────────────────────────┐
│                     User Browser                          │
│                  (HTMX + HTML + CSS)                      │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP Request/Response
                     │ (HTML Fragments)
┌────────────────────▼─────────────────────────────────────┐
│                   FastAPI Server                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │          Route Handlers (endpoints)               │    │
│  └───────┬──────────────────────────────────────────┘    │
│          │                                                │
│  ┌───────▼──────────┐  ┌─────────────────────────┐      │
│  │  Video Service   │  │  Transcription Service  │      │
│  │                  │  │                         │      │
│  │  - Upload        │  │  - faster-whisper       │      │
│  │  - Trim (ffmpeg) │  │  - Word search          │      │
│  │  - Storage       │  │  - Timestamp extraction │      │
│  └──────────────────┘  └─────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  File Storage   │
            │  - uploads/     │
            │  - outputs/     │
            │  - transcripts/ │
            └─────────────────┘
```

### 3.2 データフロー

```
1. Upload Video
   User → FastAPI → Save to uploads/

2. Transcribe
   FastAPI → faster-whisper → Extract audio → Transcribe
   → Save transcript with timestamps

3. Search Word
   User input → Search in transcript → Find timestamps

4. Trim Video
   Timestamps → ffmpeg → Trim video → Save to outputs/

5. Download
   User → Download trimmed video
```

## 4. APIエンドポイント設計

### 4.1 ページ表示

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/` | メインページ表示 | HTML |

### 4.2 動画処理

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| POST | `/upload` | 動画アップロード | multipart/form-data | HTML fragment (upload status) |
| POST | `/transcribe/{video_id}` | 文字起こし実行（word-level timestamps） | - | HTML fragment (transcript) |
| POST | `/search` | 単語検索（word-level） | form (video_id, keyword) | HTML fragment (search results) |
| POST | `/trim` | 動画切り抜き＆直接レスポンス | form (video_id, start, end) | video/mp4 (streaming) |

### 4.3 ステータス確認

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/status/{task_id}` | 処理状況確認 | HTML fragment (progress) |

## 5. データモデル

### 5.1 Video

```python
class VideoMetadata:
    id: str  # UUID
    filename: str
    filepath: str
    uploaded_at: datetime
    duration: float  # seconds
    status: VideoStatus  # UPLOADED, TRANSCRIBING, READY, ERROR
```

### 5.2 Transcript (with word-level timestamps)

```python
class WordTimestamp:
    word: str
    start: float  # seconds
    end: float
    probability: float  # confidence score

class TranscriptSegment:
    start: float  # seconds
    end: float
    text: str
    words: List[WordTimestamp]  # Word-level timestamps

class Transcript:
    video_id: str
    segments: List[TranscriptSegment]
    language: str
    created_at: datetime
```

### 5.3 SearchResult (word-level)

```python
class WordMatch:
    word: str
    start: float  # Word start time
    end: float    # Word end time
    context: str  # Surrounding text for context
    segment_index: int

class SearchResult:
    keyword: str
    matches: List[WordMatch]
    total_matches: int
```

### 5.4 TrimRequest

```python
class TrimRequest:
    video_id: str
    start_time: float
    end_time: float
    # No output_path needed - video is returned directly as response
```

## 6. UI設計

### 6.1 メインページ構成

```
┌────────────────────────────────────────────────┐
│              kotoba-cutouter                    │
├────────────────────────────────────────────────┤
│                                                 │
│  [Step 1] 動画アップロード                      │
│  ┌──────────────────────────────────────────┐  │
│  │  ファイルを選択  [Browse...]              │  │
│  │  [Upload]                                 │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  [Step 2] 文字起こし                            │
│  ┌──────────────────────────────────────────┐  │
│  │  動画: example.mp4                        │  │
│  │  [文字起こしを開始]                       │  │
│  │  ⏳ 処理中... (HTMX polling)             │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  [Step 3] 単語検索                              │
│  ┌──────────────────────────────────────────┐  │
│  │  検索ワード: [_________] [Search]        │  │
│  │                                           │  │
│  │  検索結果:                                │  │
│  │  - 00:15 - 00:18: "こんにちは"          │  │
│  │    [この区間を切り抜く]                  │  │
│  │  - 00:45 - 00:48: "こんにちは"          │  │
│  │    [この区間を切り抜く]                  │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  [Step 4] ダウンロード                          │
│  ┌──────────────────────────────────────────┐  │
│  │  切り抜き完了!                            │  │
│  │  [Download video]                         │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

### 6.2 HTMX使用パターン

1. **ファイルアップロード**
   - `hx-post="/upload"` でフォーム送信
   - `hx-target="#upload-result"` で結果を挿入
   - アップロード中はスピナー表示

2. **文字起こし処理**
   - `hx-post="/transcribe/{video_id}"` で開始
   - `hx-trigger="click"` でボタンクリック時に実行
   - ポーリングで進捗状況を更新

3. **単語検索**
   - `hx-post="/search"` でリアルタイム検索
   - `hx-trigger="keyup changed delay:500ms"` で入力時に自動検索
   - 結果をリスト形式で表示

4. **動画切り抜き＆ダウンロード**
   - `hx-post="/trim"` で切り抜き実行
   - レスポンスとして直接動画ファイルを返す（ストリーミング）
   - 一時ファイルは自動クリーンアップ

## 7. ディレクトリ構造

```
kotoba-cutouter/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── models.py               # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py           # Page rendering endpoints
│   │   ├── video.py           # Video upload/download endpoints
│   │   ├── transcription.py  # Transcription endpoints
│   │   └── search.py          # Search endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── video_service.py  # Video processing logic
│   │   ├── transcription_service.py  # faster-whisper integration
│   │   └── storage_service.py  # File storage management
│   └── templates/
│       ├── base.html          # Base template
│       ├── index.html         # Main page
│       └── components/        # HTMX components
│           ├── upload_form.html
│           ├── transcript_display.html
│           └── search_results.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js             # Minimal client-side JS if needed
├── uploads/                   # Uploaded videos (gitignore)
├── transcripts/               # Transcript JSON files (gitignore)
├── temp/                      # Temporary trimmed videos (gitignore, auto-cleanup)
├── docs/
│   ├── design.md             # This file
│   └── architecture.md       # Architecture details
├── tests/
│   ├── test_video_service.py
│   ├── test_transcription_service.py
│   └── test_api.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## 8. 実装計画

### Phase 1: 基本セットアップ

- [ ] FastAPI基本構造の構築
- [ ] テンプレートエンジン（Jinja2）の設定
- [ ] ファイルアップロード機能の実装
- [ ] 静的ファイル配信の設定

### Phase 2: 音声認識機能（word-level timestamp対応）

- [ ] faster-whisper統合
- [ ] 動画から音声抽出（ffmpeg）
- [ ] **word_timestamps=True で文字起こし処理の実装**
- [ ] **単語レベルタイムスタンプ付きトランスクリプトの生成**
- [ ] トランスクリプトのJSON保存

### Phase 3: 検索機能（word-level対応）

- [ ] **トランスクリプト内での単語レベル検索**
- [ ] **word.word フィールドでのマッチング**
- [ ] 検索結果の表示（単語+コンテキスト）
- [ ] 正確なタイムスタンプ情報の抽出

### Phase 4: 動画切り抜き機能（ストリーミング対応）

- [ ] **subprocessでffmpegコマンドを直接実行**
- [ ] 指定区間での動画トリミング（一時ファイル）
- [ ] **FileResponseでのストリーミング配信**
- [ ] **一時ファイルの自動クリーンアップ**

### Phase 5: UI/UX改善

- [ ] HTMXによるインタラクティブUI
- [ ] リアルタイム進捗表示
- [ ] エラーハンドリングとユーザーフィードバック
- [ ] レスポンシブデザイン

### Phase 6: 最適化とテスト

- [ ] パフォーマンス最適化
- [ ] ユニットテストの作成
- [ ] 統合テストの作成
- [ ] ドキュメント整備

## 9. 技術的考慮事項

### 9.1 パフォーマンス

- **非同期処理**: 文字起こしと動画処理は時間がかかるため、バックグラウンドタスクとして実行
- **ストリーミング**: 大きなファイルのアップロードには chunked upload を検討
- **キャッシング**: 同じ動画の再処理を避けるため、トランスクリプトをキャッシュ

### 9.2 セキュリティ

- **ファイルサイズ制限**: 最大アップロードサイズを設定（例: 500MB）
- **ファイルタイプ検証**: 動画ファイルのみを許可
- **パス トラバーサル対策**: ファイル名のサニタイズ
- **一時ファイル削除**: 処理後の自動クリーンアップ

### 9.3 スケーラビリティ

- **ファイルストレージ**: 将来的にはS3などのオブジェクトストレージに移行可能な設計
- **タスクキュー**: Celery等のタスクキューシステムの導入を検討
- **モデルロード**: faster-whisperモデルの起動時一度だけロード（メモリ効率化）

## 10. 参考資料

### faster-whisper

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [Pythonのfaster-whisperで文字起こしをする方法](https://kodoloom.com/how-to-transcribe-an-audio-file-in-python/)
- [faster-whisperを導入、音声を文字に起こしてみよう](https://xtech.nikkei.com/atcl/nxt/column/18/03410/111400001/)

### FastAPI + HTMX

- [Using HTMX with FastAPI](https://testdriven.io/blog/fastapi-htmx/)
- [FastAPI and HTMX: A Modern Approach to Full Stack](https://dev.to/jaydevm/fastapi-and-htmx-a-modern-approach-to-full-stack-bma)
- [「FastAPI + htmxが最強説」](https://zenn.dev/livetoon/articles/04dccf642d324c)

### FFmpeg + Python

- [ffmpeg-pythonで動画をトリミング](https://qiita.com/cress_cc/items/c74d11b0bdcb0fbd6256)
- [FFmpegで指定時間でカットするまとめ](https://nico-lab.net/cutting_ffmpeg/)
