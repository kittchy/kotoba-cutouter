# kotoba-cutouter

動画から特定の単語が発言された区間を自動検知して切り抜くWebアプリケーション

## 概要

faster-whisperの**単語レベルタイムスタンプ**を使用した高精度な動画切り抜きツール。

### 主な機能

- 🎤 単語レベルの高精度な文字起こし
- 🔍 任意の単語をピンポイントで検索
- ✂️ 該当区間を自動で切り抜き
- 💾 切り抜いた動画を即座にダウンロード

## 技術スタック

- **バックエンド**: FastAPI + faster-whisper
- **フロントエンド**: HTMX + Jinja2
- **動画処理**: FFmpeg

## セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd kotoba-cutouter

# 起動
docker-compose up

# 開発モード（ホットリロード）
docker-compose --profile dev up app-dev
```

ブラウザで http://localhost:8000 にアクセス

## 使い方

1. 動画をアップロード
2. 文字起こしを実行
3. 単語を検索
4. 該当区間を切り抜き
5. ダウンロード

## 開発

```bash
# テスト
pytest tests/

# フォーマット
ruff format src/

# リント
ruff check src/
```

## ドキュメント

詳細は以下を参照：
- [設計書](docs/design.md)
- [アーキテクチャ](docs/architecture.md)
