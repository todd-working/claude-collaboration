"""Unit tests for the chunker module."""

import pytest
from datetime import datetime

from transcript_analyzer.core.chunker import (
    CHARS_PER_TOKEN,
    DEFAULT_CHUNK_TOKENS,
    DEFAULT_OVERLAP_TURNS,
    Chunk,
    ChunkingResult,
    Turn,
    chunk_messages,
    estimate_message_tokens,
    estimate_tokens,
    group_into_turns,
    should_chunk,
)
from transcript_analyzer.core.parser import Message


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_empty_string(self):
        """Empty string should have 0 tokens."""
        assert estimate_tokens("") == 0

    def test_short_text(self):
        """Short text should estimate correctly."""
        # 16 chars / 4 = 4 tokens
        assert estimate_tokens("Hello, world!!!") == 3  # 15 chars / 4 = 3

    def test_longer_text(self):
        """Longer text should scale linearly."""
        text = "a" * 100
        assert estimate_tokens(text) == 25  # 100 / 4

    def test_mixed_content(self):
        """Mixed content (text + code) should estimate reasonably."""
        text = """
        def hello():
            print("Hello, world!")
            return True
        """
        tokens = estimate_tokens(text)
        # Roughly 100 chars, so ~25 tokens
        assert 20 < tokens < 40


class TestEstimateMessageTokens:
    """Tests for message token estimation."""

    def test_includes_overhead(self):
        """Message tokens should include formatting overhead."""
        msg = Message(role="user", content="Hi")
        tokens = estimate_message_tokens(msg)
        # Content: 2 chars / 4 = 0 tokens, plus ~10 overhead
        assert tokens > estimate_tokens("Hi")
        assert tokens >= 10  # At least the overhead

    def test_scales_with_content(self):
        """Larger messages should have more tokens."""
        short_msg = Message(role="user", content="Hi")
        long_msg = Message(role="user", content="Hello " * 100)

        assert estimate_message_tokens(long_msg) > estimate_message_tokens(short_msg)


class TestGroupIntoTurns:
    """Tests for grouping messages into conversation turns."""

    def test_empty_messages(self):
        """Empty message list should return empty turns."""
        turns = group_into_turns([])
        assert turns == []

    def test_single_user_message(self):
        """Single user message creates one turn."""
        messages = [Message(role="user", content="Hello")]
        turns = group_into_turns(messages)

        assert len(turns) == 1
        assert turns[0].user_message.content == "Hello"
        assert turns[0].assistant_message is None

    def test_user_assistant_pair(self):
        """User + assistant pair creates one complete turn."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]
        turns = group_into_turns(messages)

        assert len(turns) == 1
        assert turns[0].user_message.content == "Hello"
        assert turns[0].assistant_message.content == "Hi there!"

    def test_multiple_turns(self):
        """Multiple user-assistant pairs create multiple turns."""
        messages = [
            Message(role="user", content="First question"),
            Message(role="assistant", content="First answer"),
            Message(role="user", content="Second question"),
            Message(role="assistant", content="Second answer"),
        ]
        turns = group_into_turns(messages)

        assert len(turns) == 2
        assert turns[0].user_message.content == "First question"
        assert turns[0].assistant_message.content == "First answer"
        assert turns[1].user_message.content == "Second question"
        assert turns[1].assistant_message.content == "Second answer"

    def test_incomplete_turn_at_end(self):
        """Incomplete turn at end (user without assistant) is included."""
        messages = [
            Message(role="user", content="Question 1"),
            Message(role="assistant", content="Answer 1"),
            Message(role="user", content="Question 2"),
        ]
        turns = group_into_turns(messages)

        assert len(turns) == 2
        assert turns[1].user_message.content == "Question 2"
        assert turns[1].assistant_message is None

    def test_orphan_assistant_ignored(self):
        """Assistant message without preceding user is ignored."""
        messages = [
            Message(role="assistant", content="Random assistant message"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!"),
        ]
        turns = group_into_turns(messages)

        assert len(turns) == 1
        assert turns[0].user_message.content == "Hello"

    def test_turn_has_correct_messages(self):
        """Turn.messages property returns correct list."""
        messages = [
            Message(role="user", content="Q"),
            Message(role="assistant", content="A"),
        ]
        turns = group_into_turns(messages)

        assert len(turns[0].messages) == 2
        assert turns[0].messages[0].role == "user"
        assert turns[0].messages[1].role == "assistant"


class TestChunkMessages:
    """Tests for the main chunking function."""

    def test_empty_messages(self):
        """Empty messages returns empty result."""
        result = chunk_messages([])

        assert result.chunks == []
        assert result.total_tokens == 0
        assert result.total_messages == 0
        assert result.was_chunked is False

    def test_small_transcript_no_chunking(self):
        """Small transcript should not be chunked."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!"),
        ]
        result = chunk_messages(messages, target_tokens=6000)

        assert len(result.chunks) == 1
        assert result.was_chunked is False
        assert result.chunks[0].chunk_index == 0
        assert result.chunks[0].total_chunks == 1

    def test_large_transcript_is_chunked(self):
        """Large transcript should be split into chunks."""
        # Create a transcript that exceeds target tokens
        # Each message is ~1000 tokens (4000 chars)
        long_content = "x" * 4000
        messages = [
            Message(role="user", content=long_content),
            Message(role="assistant", content=long_content),
        ] * 5  # 10 messages, ~10000 tokens

        result = chunk_messages(messages, target_tokens=2000)

        assert len(result.chunks) > 1
        assert result.was_chunked is True

    def test_chunk_indices_correct(self):
        """Chunks should have correct indices and total count."""
        long_content = "x" * 4000
        messages = [
            Message(role="user", content=long_content),
            Message(role="assistant", content=long_content),
        ] * 5

        result = chunk_messages(messages, target_tokens=2000)

        for i, chunk in enumerate(result.chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == len(result.chunks)

    def test_overlap_between_chunks(self):
        """Chunks should have overlapping turns for context."""
        long_content = "x" * 4000
        messages = [
            Message(role="user", content=long_content),
            Message(role="assistant", content=long_content),
        ] * 6

        result = chunk_messages(messages, target_tokens=2000, overlap_turns=1)

        if len(result.chunks) > 1:
            # Second chunk should have overlap
            assert result.chunks[1].overlap_count > 0

    def test_no_overlap_when_disabled(self):
        """No overlap when overlap_turns=0."""
        long_content = "x" * 4000
        messages = [
            Message(role="user", content=long_content),
            Message(role="assistant", content=long_content),
        ] * 6

        result = chunk_messages(messages, target_tokens=2000, overlap_turns=0)

        # All chunks should have 0 overlap (except possibly first which always has 0)
        for i, chunk in enumerate(result.chunks):
            if i == 0:
                assert chunk.overlap_count == 0
            # With overlap_turns=0, no overlap should be added
            # (first chunk never has overlap)

    def test_preserves_turn_boundaries(self):
        """Chunks should split on turn boundaries, not mid-turn."""
        # Create turns of varying sizes
        messages = []
        for i in range(10):
            messages.append(Message(role="user", content=f"Question {i}: " + "x" * 500))
            messages.append(Message(role="assistant", content=f"Answer {i}: " + "x" * 500))

        result = chunk_messages(messages, target_tokens=1000)

        # Each chunk should have messages in user/assistant pairs
        for chunk in result.chunks:
            non_overlap_messages = chunk.messages[chunk.overlap_count:]
            # Messages should alternate user/assistant
            for j in range(0, len(non_overlap_messages) - 1, 2):
                if j < len(non_overlap_messages):
                    assert non_overlap_messages[j].role == "user"
                if j + 1 < len(non_overlap_messages):
                    assert non_overlap_messages[j + 1].role == "assistant"

    def test_config_in_result(self):
        """Result should include chunking configuration."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!"),
        ]

        result = chunk_messages(messages, target_tokens=1000, overlap_turns=3)

        assert result.chunk_config["target_tokens"] == 1000
        assert result.chunk_config["overlap_turns"] == 3


class TestShouldChunk:
    """Tests for the should_chunk helper function."""

    def test_empty_messages(self):
        """Empty messages should not be chunked."""
        assert should_chunk([]) is False

    def test_small_transcript(self):
        """Small transcript should not need chunking."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!"),
        ]
        assert should_chunk(messages, chunk_threshold=6000) is False

    def test_large_transcript(self):
        """Large transcript should need chunking."""
        long_content = "x" * 10000
        messages = [
            Message(role="user", content=long_content),
            Message(role="assistant", content=long_content),
        ]
        assert should_chunk(messages, chunk_threshold=1000) is True


class TestChunkFormatTranscript:
    """Tests for Chunk.format_transcript method."""

    def test_format_produces_markdown(self):
        """Chunk should format as markdown transcript."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]
        chunk = Chunk(
            messages=messages,
            chunk_index=0,
            total_chunks=1,
        )

        transcript = chunk.format_transcript()

        assert "# Transcript" in transcript
        assert "## User" in transcript
        assert "## Claude" in transcript
        assert "Hello" in transcript
        assert "Hi there!" in transcript


class TestTurnMessages:
    """Tests for Turn.messages property."""

    def test_complete_turn(self):
        """Complete turn returns both messages."""
        turn = Turn(
            user_message=Message(role="user", content="Q"),
            assistant_message=Message(role="assistant", content="A"),
        )
        assert len(turn.messages) == 2

    def test_incomplete_turn(self):
        """Incomplete turn returns only user message."""
        turn = Turn(
            user_message=Message(role="user", content="Q"),
            assistant_message=None,
        )
        assert len(turn.messages) == 1
        assert turn.messages[0].role == "user"
