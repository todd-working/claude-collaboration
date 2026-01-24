"""JSONL session file parser for Claude Code transcripts."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime | None = None
    session_id: str | None = None
    cwd: str | None = None


@dataclass
class SessionMetadata:
    """Metadata about a session file."""

    session_id: str
    file_path: Path
    modified_at: datetime
    size_bytes: int
    project_path: str | None = None


def extract_content(message_data: dict) -> str | None:
    """
    Extract text content from a message.

    Handles both formats:
    - content as string
    - content as array of {type: "text", text: "..."} blocks
    """
    content = message_data.get("content")
    if content is None:
        return None

    # String content (simple case)
    if isinstance(content, str):
        return content

    # Array content - extract text blocks
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if text:
                    texts.append(text)
        return "\n".join(texts) if texts else None

    return None


def parse_timestamp(ts: str | None) -> datetime | None:
    """Parse ISO timestamp string to datetime."""
    if not ts:
        return None
    try:
        # Handle various ISO formats
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def parse_session_file(file_path: Path) -> Iterator[Message]:
    """
    Parse a Claude Code session JSONL file and yield messages.

    Args:
        file_path: Path to the .jsonl session file

    Yields:
        Message objects for each user/assistant exchange
    """
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            message_data = data.get("message", {})
            content = extract_content(message_data)

            if not content:
                continue

            yield Message(
                role="user" if msg_type == "user" else "assistant",
                content=content,
                timestamp=parse_timestamp(data.get("timestamp")),
                session_id=data.get("sessionId"),
                cwd=data.get("cwd"),
            )


def format_transcript(messages: list[Message], include_metadata: bool = False) -> str:
    """
    Format messages as a readable markdown transcript.

    Args:
        messages: List of Message objects
        include_metadata: Whether to include timestamps and metadata

    Returns:
        Markdown-formatted transcript string
    """
    lines = ["# Transcript", ""]

    if messages and messages[0].session_id:
        lines.append(f"Session: {messages[0].session_id}")
        lines.append("")

    lines.append("---")
    lines.append("")

    for msg in messages:
        header = "## User" if msg.role == "user" else "## Claude"
        lines.append(header)

        if include_metadata and msg.timestamp:
            lines.append(f"*{msg.timestamp.isoformat()}*")

        lines.append("")
        lines.append(msg.content)
        lines.append("")

    return "\n".join(lines)


def extract_transcript(file_path: Path, include_metadata: bool = False) -> str:
    """
    Extract a readable transcript from a session file.

    Args:
        file_path: Path to the .jsonl session file
        include_metadata: Whether to include timestamps

    Returns:
        Markdown-formatted transcript
    """
    messages = list(parse_session_file(file_path))
    return format_transcript(messages, include_metadata)


def get_session_metadata(file_path: Path) -> SessionMetadata:
    """
    Get metadata about a session file without fully parsing it.

    Args:
        file_path: Path to the .jsonl session file

    Returns:
        SessionMetadata object
    """
    stat = file_path.stat()

    # Try to extract session ID from first message
    session_id = file_path.stem  # Default to filename
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if "sessionId" in data:
                    session_id = data["sessionId"]
                    break
            except json.JSONDecodeError:
                continue

    # Extract project path from parent directory name
    # Format: -Users-username-path-to-project
    parent_name = file_path.parent.name
    project_path = None
    if parent_name.startswith("-"):
        # Convert dash-separated path back to real path
        parts = parent_name.split("-")
        if len(parts) > 1:
            project_path = "/" + "/".join(parts[1:])

    return SessionMetadata(
        session_id=session_id,
        file_path=file_path,
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        size_bytes=stat.st_size,
        project_path=project_path,
    )


def find_sessions(
    base_path: Path | None = None,
    project_filter: str | None = None,
    days: int = 30,
    limit: int = 20,
) -> list[SessionMetadata]:
    """
    Find Claude Code session files.

    Args:
        base_path: Base path to search (defaults to ~/.claude/projects)
        project_filter: Filter sessions by project path substring
        days: Only include sessions modified within this many days
        limit: Maximum number of sessions to return

    Returns:
        List of SessionMetadata, sorted by modification time (newest first)
    """
    if base_path is None:
        base_path = Path.home() / ".claude" / "projects"

    if not base_path.exists():
        return []

    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    sessions = []

    for jsonl_file in base_path.rglob("*.jsonl"):
        stat = jsonl_file.stat()
        if stat.st_mtime < cutoff:
            continue

        metadata = get_session_metadata(jsonl_file)

        if project_filter and metadata.project_path:
            if project_filter.lower() not in metadata.project_path.lower():
                continue

        sessions.append(metadata)

    # Sort by modification time, newest first
    sessions.sort(key=lambda s: s.modified_at, reverse=True)

    return sessions[:limit]
