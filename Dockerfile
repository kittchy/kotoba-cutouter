FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

COPY src/ ./src/
COPY static/ ./static/

RUN mkdir -p uploads transcripts temp

ENV PYTHONUNBUFFERED=1
ENV UPLOAD_DIR=/app/uploads
ENV TRANSCRIPT_DIR=/app/transcripts
ENV TEMP_DIR=/app/temp
ENV WHISPER_MODEL_SIZE=base
ENV WHISPER_DEVICE=cpu

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
