"""Data models for the application"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class VideoStatus(str, Enum):
    """Video processing status"""

    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    READY = "ready"
    ERROR = "error"


class VideoMetadata(BaseModel):
    """Video file metadata"""

    id: str  # UUID
    filename: str
    filepath: str
    uploaded_at: datetime
    duration: Optional[float] = None  # seconds
    status: VideoStatus = VideoStatus.UPLOADED


class WordTimestamp(BaseModel):
    """Word-level timestamp from faster-whisper"""

    word: str
    start: float  # seconds
    end: float  # seconds
    probability: float  # confidence score


class TranscriptSegment(BaseModel):
    """Transcript segment with word-level timestamps"""

    start: float  # seconds
    end: float  # seconds
    text: str
    words: list[WordTimestamp]  # Word-level timestamps


class Transcript(BaseModel):
    """Complete transcript with word-level timestamps"""

    video_id: str
    segments: list[TranscriptSegment]
    language: str
    created_at: datetime


class WordMatch(BaseModel):
    """Word match result from search"""

    word: str
    start: float  # Word start time
    end: float  # Word end time
    context: str  # Surrounding text for context
    segment_index: int


class SearchResult(BaseModel):
    """Search result containing word matches"""

    keyword: str
    matches: list[WordMatch]
    total_matches: int


class TrimRequest(BaseModel):
    """Request to trim video"""

    video_id: str
    start_time: float
    end_time: float
