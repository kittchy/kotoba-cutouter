"""Search endpoints for word-level keyword search"""

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

from src.services.transcription_service import TranscriptionService

router = APIRouter()

# Context padding in seconds (before and after the matched word)
CONTEXT_PADDING = 2.0


@router.post("/search", response_class=HTMLResponse)
async def search_keyword(
    video_id: str = Form(...),
    keyword: str = Form(""),
):
    """
    Search for keyword in transcript using word-level timestamps

    Args:
        video_id: Video ID
        keyword: Keyword to search for

    Returns:
        HTML fragment with search results
    """
    # Empty keyword returns empty results
    if not keyword.strip():
        return '<div id="search-results"></div>'

    # Load transcript
    transcript = TranscriptionService.load_transcript(video_id)
    if not transcript:
        return '''<div class="error htmx-added">
            <h3 style="margin: 0 0 0.5rem 0;">❌ 文字起こしデータが見つかりません</h3>
            <p style="margin: 0;">まず文字起こし処理を実行してください。</p>
        </div>'''

    # Search for keyword in segment text (not individual words)
    # This allows matching phrases that span multiple words
    matches = []
    keyword_lower = keyword.lower().strip()

    for seg_idx, segment in enumerate(transcript.segments):
        # Check if keyword exists in segment text
        if keyword_lower not in segment.text.lower():
            continue

        # Find consecutive words that match the keyword
        words = segment.words

        # Try all possible consecutive word combinations
        for i in range(len(words)):
            for j in range(i + 1, len(words) + 1):
                consecutive_words = words[i:j]

                # Combine words (removing spaces that might be in word.word)
                combined_text = "".join([w.word.strip() for w in consecutive_words])

                # Check if this combination matches the keyword exactly
                if keyword_lower == combined_text.lower():
                    # Found a match - use the exact time range of matched words
                    matches.append({
                        "word": combined_text,
                        "start": consecutive_words[0].start,
                        "end": consecutive_words[-1].end,
                        "context": segment.text,
                        "segment_index": seg_idx,
                    })
                    # Only take the shortest match for each position
                    break

    # No matches found
    if not matches:
        return f"""
        <div id="search-results">
            <div class="info htmx-added">
                <p>"{keyword}" is not found in the transcript.</p>
            </div>
        </div>
        """

    # Render search results with trim buttons
    results_html = f"""
    <div id="search-results">
        <div class="success htmx-added">
            <p>Found {len(matches)} match(es) for "{keyword}"</p>
        </div>
        <div class="search-results-list">
    """

    for i, match in enumerate(matches):
        # Use exact word boundaries without padding
        start_time = match["start"]
        end_time = match["end"]

        # Format timestamps for display
        start_display = _format_timestamp(start_time)
        end_display = _format_timestamp(end_time)

        results_html += f"""
        <div class="search-result-item">
            <div class="result-header">
                <span class="result-time">{start_display} - {end_display}</span>
                <span class="result-word">"{match["word"]}"</span>
            </div>
            <div class="result-context">
                <p>{match["context"]}</p>
            </div>
            <div class="result-actions">
                <form action="/trim" method="post">
                    <input type="hidden" name="video_id" value="{video_id}">
                    <input type="hidden" name="start_time" value="{start_time}">
                    <input type="hidden" name="end_time" value="{end_time}">
                    <button type="submit" class="primary">
                        📥 この区間をダウンロード
                    </button>
                </form>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #666;">
                    切り抜き範囲: {_format_timestamp(start_time)} - {_format_timestamp(end_time)} (キーワード部分のみ)
                </p>
            </div>
        </div>
        """

    results_html += """
        </div>
    </div>
    """
    return results_html


def _format_timestamp(seconds: float) -> str:
    """
    Format seconds to MM:SS or HH:MM:SS format

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - total_seconds) * 100)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{millis:02d}"
