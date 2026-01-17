# kotoba-cutouter

動画から特定の単語が発言された区間を自動検知し、その部分を切り抜くWebアプリケーション

## 概要

kotoba-cutouter（コトバ・カットアウター）は、faster-whisperによる高速な音声認識とFastAPI + HTMXによる軽量なWebインターフェースを組み合わせた動画切り抜きツールです。

### 主な機能

- 🎬 **動画アップロード**: MP4, MOV, AVI等の動画ファイルをアップロード
- 🎤 **自動文字起こし（word-level timestamp対応）**: faster-whisperによる単語レベルの高精度な音声認識
- 🔍 **単語検索**: 文字起こし結果から任意の単語・フレーズを**ピンポイント**で検索
- ✂️ **自動切り抜き**: 該当区間を自動検出して動画を切り抜き
- 💾 **即座ダウンロード**: 切り抜いた動画をストリーミングで即座にダウンロード

### 🌟 word-level timestampの強み

従来のセグメント単位ではなく、**単語レベルの正確なタイムスタンプ**を使用：

- ✅ 任意の単語を**ピンポイント**で切り出せる
- ✅ 不要な前後の発言を含まない高精度な切り抜き
- ✅ 長いセグメントでも特定の単語だけを抽出可能

例：「こんにちは、今日はいい天気ですね」という文から、「こんにちは」だけを正確に切り出せます。

## 技術スタック

- **バックエンド**: FastAPI, faster-whisper
- **フロントエンド**: HTMX, Jinja2
- **音声認識**: faster-whisper (OpenAI Whisperの高速化版)
- **動画処理**: FFmpeg (subprocess経由で直接実行)

## ドキュメント

詳細な設計と実装については、以下のドキュメントを参照してください：

- [設計書](docs/design.md) - システム設計、機能要件、実装計画
- [アーキテクチャ](docs/architecture.md) - アーキテクチャ詳細、データフロー、実装パターン

## セットアップ

### 🐳 Docker（推奨）

Dockerを使うと、FFmpegや依存関係が自動的にセットアップされます。

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd kotoba-cutouter
```

2. Docker Composeで起動:
```bash
docker-compose up
```

3. ブラウザで http://localhost:8000 にアクセス

**開発モード（ホットリロード対応）:**
```bash
docker-compose --profile dev up app-dev
```

### ローカル環境

#### 前提条件

- Python 3.11以上
- [uv](https://github.com/astral-sh/uv)（推奨）
- FFmpeg（システムにインストール済みであること）

#### FFmpegのインストール

**macOS**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows**:
[FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロードしてインストール

#### インストール

1. リポジトリをクローン:
```bash
git clone <repository-url>
cd kotoba-cutouter
```

2. 依存関係をインストール:
```bash
uv sync
```

3. 必要なディレクトリを作成:
```bash
mkdir -p uploads transcripts temp static/css static/js
```

4. 開発サーバーの起動:
```bash
uvicorn src.main:app --reload
```

5. ブラウザで http://localhost:8000 にアクセス

## 使い方

### 基本的な使い方

1. **動画をアップロード**: 対象の動画ファイルを選択してアップロード
2. **文字起こし実行**: 「文字起こしを開始」ボタンをクリック
   - word-level timestampで単語レベルの正確な文字起こしを実行
   - 処理には数分かかる場合があります
3. **単語を検索**: 検索フォームに切り抜きたいシーンの単語を入力
   - 単語レベルで正確にマッチング
4. **区間を選択**: 検索結果から切り抜きたい区間を選択
   - 各単語の正確なタイムスタンプが表示されます
5. **切り抜き実行**: 「この区間を切り抜く」ボタンをクリック
6. **即座ダウンロード**: 切り抜いた動画がストリーミングで即座にダウンロードされます

## プロジェクト構造

```
kotoba-cutouter/
├── src/                    # ソースコード
│   ├── main.py            # FastAPIアプリケーション
│   ├── config.py          # 設定
│   ├── models.py          # データモデル
│   ├── routers/           # APIエンドポイント
│   ├── services/          # ビジネスロジック
│   └── templates/         # HTMLテンプレート
├── static/                # 静的ファイル
│   ├── css/
│   └── js/
├── uploads/               # アップロードされた動画
├── outputs/               # 切り抜いた動画
├── transcripts/           # 文字起こし結果
├── docs/                  # ドキュメント
├── tests/                 # テスト
└── pyproject.toml         # プロジェクト設定
```

## 設定

環境変数で以下の設定をカスタマイズ可能:

```env
UPLOAD_DIR=uploads              # アップロードディレクトリ
OUTPUT_DIR=outputs              # 出力ディレクトリ
TRANSCRIPT_DIR=transcripts      # 文字起こし結果ディレクトリ
MAX_FILE_SIZE=524288000         # 最大ファイルサイズ (500MB)
WHISPER_MODEL_SIZE=base         # Whisperモデルサイズ (tiny/base/small/medium/large)
WHISPER_DEVICE=cpu              # 処理デバイス (cpu/cuda)
```

## モデルサイズについて

faster-whisperは複数のモデルサイズをサポートしています:

| モデル | 精度 | 速度 | メモリ使用量 |
|--------|------|------|--------------|
| tiny   | 低   | 最速 | 最小         |
| base   | 中   | 速い | 小           |
| small  | 高   | 中   | 中           |
| medium | 最高 | 遅い | 大           |
| large  | 最高 | 最遅 | 最大         |

デフォルトは `base` モデルで、精度と速度のバランスが取れています。

## トラブルシューティング

### FFmpegが見つからない

```
Error: FFmpeg not found
```

→ FFmpegがシステムにインストールされているか確認してください

### メモリ不足エラー

```
Error: Out of memory
```

→ より小さいWhisperモデルサイズ（`tiny` または `base`）を使用してください

### ファイルサイズが大きすぎる

```
Error: File too large
```

→ 最大ファイルサイズは500MBです。動画を圧縮するか、短い動画に分割してください

## 開発

### テストの実行

```bash
pytest tests/
```

### コードフォーマット

```bash
ruff format src/
```

### リントチェック

```bash
ruff check src/
```

## ライセンス

MIT License

## 参考資料

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [FastAPI](https://fastapi.tiangolo.com/)
- [HTMX](https://htmx.org/)
- [FFmpeg](https://ffmpeg.org/)

## TODO

実装予定の機能については [docs/design.md](docs/design.md#8-実装計画) を参照してください。
