"""Intelligent chunking for transcript analysis.

Splits long transcripts into manageable chunks at conversation turn boundaries,
enabling map-reduce style analysis with smaller models.
"""

import logging
from dataclasses import dataclass, field

from .parser import Message, format_transcript

logger = logging.getLogger(__name__)

# Default chunking configuration
DEFAULT_CHUNK_TOKENS = 6000  # ~24k chars, leaving room for prompts
DEFAULT_OVERLAP_TURNS = 2  # Number of turns to overlap between chunks
CHARS_PER_TOKEN = 4  # Rough estimate: ~4 characters per token


@dataclass
class Turn:
    """A conversation turn (user message + optional assistant response)."""

    user_message: Message
    assistant_message: Message | None = None
    estimated_tokens: int = 0

    @property
    def messages(self) -> list[Message]:
        """Return messages in this turn."""
        if self.assistant_message:
            return [self.user_message, self.assistant_message]
        return [self.user_message]


@dataclass
class Chunk:
    """A chunk of conversation for analysis."""

    messages: list[Message]
    chunk_index: int
    total_chunks: int
    overlap_count: int = 0  # Messages overlapping from previous chunk
    estimated_tokens: int = 0
    context_summary: str = ""  # Summary of prior context (if any)

    def format_transcript(self, include_metadata: bool = False) -> str:
        """Format this chunk as a markdown transcript."""
        return format_transcript(self.messages, include_metadata)


@dataclass
class ChunkingResult:
    """Result of chunking operation."""

    chunks: list[Chunk]
    total_tokens: int
    total_messages: int
    was_chunked: bool  # False if transcript fit in single pass
    chunk_config: dict = field(default_factory=dict)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.

    Uses a simple heuristic of ~4 characters per token.
    This is a reasonable approximation for English text and code.

    Args:
        text: Input text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // CHARS_PER_TOKEN


def estimate_message_tokens(message: Message) -> int:
    """Estimate tokens for a single message including overhead."""
    # Base content tokens
    tokens = estimate_tokens(message.content)

    # Add small overhead for role/formatting (~10 tokens)
    tokens += 10

    return tokens


def group_into_turns(messages: list[Message]) -> list[Turn]:
    """
    Group messages into conversation turns.

    A turn consists of a user message followed by an optional assistant response.
    This maintains conversational coherence when chunking.

    Args:
        messages: List of Message objects

    Returns:
        List of Turn objects
    """
    turns: list[Turn] = []
    current_turn: Turn | None = None

    for msg in messages:
        if msg.role == "user":
            # Start a new turn
            if current_turn is not None:
                turns.append(current_turn)
            current_turn = Turn(
                user_message=msg,
                estimated_tokens=estimate_message_tokens(msg),
            )
        elif msg.role == "assistant" and current_turn is not None:
            # Add to current turn
            current_turn.assistant_message = msg
            current_turn.estimated_tokens += estimate_message_tokens(msg)

    # Don't forget the last turn
    if current_turn is not None:
        turns.append(current_turn)

    return turns


def chunk_messages(
    messages: list[Message],
    target_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_turns: int = DEFAULT_OVERLAP_TURNS,
) -> ChunkingResult:
    """
    Split messages into chunks at turn boundaries.

    Groups user+assistant pairs as "turns" to maintain coherence.
    Adds overlap from previous chunk for context continuity.

    Args:
        messages: List of Message objects to chunk
        target_tokens: Target token count per chunk (default: 6000)
        overlap_turns: Number of turns to overlap between chunks (default: 2)

    Returns:
        ChunkingResult with chunks and metadata
    """
    if not messages:
        return ChunkingResult(
            chunks=[],
            total_tokens=0,
            total_messages=0,
            was_chunked=False,
        )

    # Estimate total tokens
    total_text = format_transcript(messages)
    total_tokens = estimate_tokens(total_text)

    # Check if chunking is needed (use 80% threshold for safety margin)
    threshold = int(target_tokens * 0.8)
    if total_tokens <= threshold:
        # Single chunk - no need to split
        chunk = Chunk(
            messages=messages,
            chunk_index=0,
            total_chunks=1,
            overlap_count=0,
            estimated_tokens=total_tokens,
        )
        return ChunkingResult(
            chunks=[chunk],
            total_tokens=total_tokens,
            total_messages=len(messages),
            was_chunked=False,
            chunk_config={
                "target_tokens": target_tokens,
                "overlap_turns": overlap_turns,
            },
        )

    # Group messages into turns
    turns = group_into_turns(messages)

    if not turns:
        return ChunkingResult(
            chunks=[],
            total_tokens=total_tokens,
            total_messages=len(messages),
            was_chunked=False,
        )

    logger.info(
        f"Chunking {len(messages)} messages ({len(turns)} turns, "
        f"~{total_tokens} tokens) with target {target_tokens} tokens/chunk"
    )

    # Build chunks
    chunks: list[Chunk] = []
    current_chunk_turns: list[Turn] = []
    current_tokens = 0
    overlap_turns_for_next: list[Turn] = []

    for i, turn in enumerate(turns):
        # Check if adding this turn would exceed target
        if current_tokens + turn.estimated_tokens > target_tokens and current_chunk_turns:
            # Finalize current chunk
            chunk_messages_list = []
            overlap_count = 0

            # Add overlap from previous chunk
            for overlap_turn in overlap_turns_for_next:
                chunk_messages_list.extend(overlap_turn.messages)
                overlap_count += len(overlap_turn.messages)

            # Add current chunk turns
            for chunk_turn in current_chunk_turns:
                chunk_messages_list.extend(chunk_turn.messages)

            chunk = Chunk(
                messages=chunk_messages_list,
                chunk_index=len(chunks),
                total_chunks=0,  # Will be updated later
                overlap_count=overlap_count,
                estimated_tokens=sum(t.estimated_tokens for t in current_chunk_turns),
            )
            chunks.append(chunk)

            # Save overlap turns for next chunk
            overlap_turns_for_next = current_chunk_turns[-overlap_turns:] if overlap_turns > 0 else []

            # Start new chunk
            current_chunk_turns = [turn]
            current_tokens = turn.estimated_tokens
        else:
            # Add turn to current chunk
            current_chunk_turns.append(turn)
            current_tokens += turn.estimated_tokens

    # Don't forget the last chunk
    if current_chunk_turns:
        chunk_messages_list = []
        overlap_count = 0

        # Add overlap from previous chunk
        for overlap_turn in overlap_turns_for_next:
            chunk_messages_list.extend(overlap_turn.messages)
            overlap_count += len(overlap_turn.messages)

        # Add current chunk turns
        for chunk_turn in current_chunk_turns:
            chunk_messages_list.extend(chunk_turn.messages)

        chunk = Chunk(
            messages=chunk_messages_list,
            chunk_index=len(chunks),
            total_chunks=0,  # Will be updated later
            overlap_count=overlap_count,
            estimated_tokens=sum(t.estimated_tokens for t in current_chunk_turns),
        )
        chunks.append(chunk)

    # Update total_chunks in each chunk
    total_chunks = len(chunks)
    for chunk in chunks:
        chunk.total_chunks = total_chunks

    logger.info(f"Created {total_chunks} chunks from {len(messages)} messages")

    return ChunkingResult(
        chunks=chunks,
        total_tokens=total_tokens,
        total_messages=len(messages),
        was_chunked=True,
        chunk_config={
            "target_tokens": target_tokens,
            "overlap_turns": overlap_turns,
        },
    )


def should_chunk(
    messages: list[Message],
    chunk_threshold: int = DEFAULT_CHUNK_TOKENS,
) -> bool:
    """
    Determine if a transcript should be chunked.

    Args:
        messages: List of Message objects
        chunk_threshold: Token threshold for chunking

    Returns:
        True if transcript should be chunked, False otherwise
    """
    if not messages:
        return False

    total_text = format_transcript(messages)
    total_tokens = estimate_tokens(total_text)

    # Use 80% threshold for safety margin
    return total_tokens > int(chunk_threshold * 0.8)
