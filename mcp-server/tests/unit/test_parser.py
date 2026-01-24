"""Tests for JSONL parser."""

import json
import tempfile
from pathlib import Path

from transcript_analyzer.core.parser import (
    extract_content,
    extract_transcript,
    parse_session_file,
)


def test_extract_content_string():
    """Test extracting content from string format."""
    message = {"content": "Hello world"}
    assert extract_content(message) == "Hello world"


def test_extract_content_array():
    """Test extracting content from array format."""
    message = {
        "content": [
            {"type": "text", "text": "First part"},
            {"type": "text", "text": "Second part"},
        ]
    }
    assert extract_content(message) == "First part\nSecond part"


def test_extract_content_mixed_array():
    """Test extracting content from array with non-text blocks."""
    message = {
        "content": [
            {"type": "text", "text": "Text content"},
            {"type": "tool_use", "name": "some_tool"},
        ]
    }
    assert extract_content(message) == "Text content"


def test_extract_content_none():
    """Test extracting content when none present."""
    assert extract_content({}) is None
    assert extract_content({"content": None}) is None


def test_parse_session_file():
    """Test parsing a session file."""
    # Create a temporary session file
    session_data = [
        {
            "type": "user",
            "message": {"role": "user", "content": "Hello Claude"},
            "sessionId": "test-session",
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Hello! How can I help?"}],
            },
        },
        {"type": "file_history", "data": {}},  # Should be skipped
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for item in session_data:
            f.write(json.dumps(item) + "\n")
        temp_path = Path(f.name)

    try:
        messages = list(parse_session_file(temp_path))

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello Claude"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hello! How can I help?"
    finally:
        temp_path.unlink()


def test_extract_transcript():
    """Test extracting formatted transcript."""
    session_data = [
        {
            "type": "user",
            "message": {"content": "What is 2+2?"},
            "sessionId": "math-session",
        },
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "2+2 equals 4."}]},
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for item in session_data:
            f.write(json.dumps(item) + "\n")
        temp_path = Path(f.name)

    try:
        transcript = extract_transcript(temp_path)

        assert "# Transcript" in transcript
        assert "## User" in transcript
        assert "What is 2+2?" in transcript
        assert "## Claude" in transcript
        assert "2+2 equals 4." in transcript
    finally:
        temp_path.unlink()
