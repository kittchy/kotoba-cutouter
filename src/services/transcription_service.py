"""Audio transcription service using faster-whisper"""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from src.config import get_settings
from src.models import Transcript, TranscriptSegment, WordTimestamp

settings = get_settings()


class TranscriptionService:
    """Handle audio transcription using faster-whisper with word-level timestamps"""

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Initialize faster-whisper model

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to use (cpu or cuda)
        """
        self.model = WhisperModel(model_size, device=device)
        self.model_size = model_size
        self.device = device

    async def transcribe_video(
        self, video_id: str, video_path: str, language: str = "ja"
    ) -> Transcript:
        """
        Transcribe video audio to text with word-level timestamps

        Steps:
        1. Extract audio from video (ffmpeg)
        2. Run faster-whisper transcription with word_timestamps=True
        3. Generate transcript with word-level timestamps
        4. Save transcript as JSON

        Args:
            video_id: Video ID
            video_path: Path to video file
            language: Language code (default: "ja" for Japanese)

        Returns:
            Transcript object with word-level timestamps
        """
        # Extract audio from video
        audio_path = self.extract_audio(video_path)

        try:
            # Run transcription with word-level timestamps
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,  # Enable word-level timestamps
            )

            # Convert segments to our data model
            transcript_segments = []

            for segment in segments:
                # Extract word timestamps
                words = []
                if segment.words:
                    for word in segment.words:
                        words.append(
                            WordTimestamp(
                                word=word.word,
                                start=word.start,
                                end=word.end,
                                probability=word.probability,
                            )
                        )

                # Create segment
                transcript_segment = TranscriptSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    words=words,
                )
                transcript_segments.append(transcript_segment)

            # Create transcript object
            transcript = Transcript(
                video_id=video_id,
                segments=transcript_segments,
                language=info.language,
                created_at=datetime.now(),
            )

            # Save transcript as JSON
            self.save_transcript(video_id, transcript)

            return transcript

        finally:
            # Clean up temporary audio file
            if Path(audio_path).exists():
                Path(audio_path).unlink()

    @staticmethod
    def extract_audio(video_path: str) -> str:
        """
        Extract audio track from video using ffmpeg

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file
        """
        # Generate unique filename for audio
        audio_id = str(uuid.uuid4())
        audio_path = str(settings.TEMP_DIR / f"{audio_id}.wav")

        # Ensure temp directory exists
        settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Extract audio using ffmpeg
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ar",
            "16000",  # 16kHz sample rate (recommended for Whisper)
            "-ac",
            "1",  # mono
            "-vn",  # no video
            "-y",  # overwrite output file
            audio_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return audio_path

    @staticmethod
    def save_transcript(video_id: str, transcript: Transcript) -> str:
        """
        Save transcript as JSON file

        Args:
            video_id: Video ID
            transcript: Transcript object

        Returns:
            Path to saved transcript file
        """
        # Ensure transcript directory exists
        settings.TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate transcript file path
        transcript_path = settings.TRANSCRIPT_DIR / f"{video_id}.json"

        # Convert transcript to dict and save
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(
                transcript.model_dump(mode="json"),
                f,
                ensure_ascii=False,
                indent=2,
            )

        return str(transcript_path)

    @staticmethod
    def load_transcript(video_id: str) -> Optional[Transcript]:
        """
        Load transcript from JSON file

        Args:
            video_id: Video ID

        Returns:
            Transcript object, or None if not found
        """
        transcript_path = settings.TRANSCRIPT_DIR / f"{video_id}.json"

        if not transcript_path.exists():
            return None

        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Transcript(**data)
