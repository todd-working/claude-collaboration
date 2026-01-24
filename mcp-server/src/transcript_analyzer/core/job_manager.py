"""Background job manager for analysis tasks."""

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from .chunker import (
    DEFAULT_CHUNK_TOKENS,
    DEFAULT_OVERLAP_TURNS,
    chunk_messages,
    estimate_tokens,
)
from .ollama import GenerateResponse, generate_sync
from .parser import Message, extract_transcript, format_transcript, parse_session_file
from .storage import Job, JobStatus, JobType, Storage

logger = logging.getLogger(__name__)


class JobManager:
    """Manages background analysis jobs."""

    def __init__(
        self,
        storage: Storage,
        max_workers: int = 2,
        default_model: str = "qwen2.5:72b",
        default_context_size: int = 32768,
        chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
        overlap_turns: int = DEFAULT_OVERLAP_TURNS,
    ):
        """
        Initialize job manager.

        Args:
            storage: Storage instance for jobs and results
            max_workers: Maximum concurrent analysis jobs
            default_model: Default Ollama model to use
            default_context_size: Default context window size
            chunk_tokens: Target tokens per chunk for map-reduce analysis
            overlap_turns: Number of turns to overlap between chunks
        """
        self.storage = storage
        self.default_model = default_model
        self.default_context_size = default_context_size
        self.chunk_tokens = chunk_tokens
        self.overlap_turns = overlap_turns
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running_jobs: dict[str, Future] = {}

    def submit_analysis(
        self,
        job_type: JobType,
        session_file: Path,
        system_prompt: str,
        analysis_prompt_template: str,
        model: str | None = None,
        context_size: int | None = None,
        chunk_system_prompt: str | None = None,
        chunk_prompt_template: str | None = None,
        synthesis_system_prompt: str | None = None,
        synthesis_prompt_template: str | None = None,
    ) -> Job:
        """
        Submit an analysis job for background execution.

        Args:
            job_type: Type of analysis (stenographer or insight_extractor)
            session_file: Path to the session JSONL file
            system_prompt: System prompt for the model (single-pass mode)
            analysis_prompt_template: Prompt template with {transcript} placeholder
            model: Ollama model to use (defaults to default_model)
            context_size: Context window size (defaults to default_context_size)
            chunk_system_prompt: System prompt for chunk analysis (map phase)
            chunk_prompt_template: Prompt template for chunk analysis
            synthesis_system_prompt: System prompt for synthesis (reduce phase)
            synthesis_prompt_template: Prompt template for synthesis

        Returns:
            Job object with PENDING status
        """
        model = model or self.default_model
        context_size = context_size or self.default_context_size

        # Extract session info from file path
        session_id = session_file.stem
        project_path = None
        parent_name = session_file.parent.name
        if parent_name.startswith("-"):
            parts = parent_name.split("-")
            if len(parts) > 1:
                project_path = "/" + "/".join(parts[1:])

        # Create job record
        job = self.storage.create_job(job_type, session_id, project_path)

        # Submit to thread pool
        future = self._executor.submit(
            self._run_analysis,
            job.id,
            session_file,
            system_prompt,
            analysis_prompt_template,
            model,
            context_size,
            chunk_system_prompt,
            chunk_prompt_template,
            synthesis_system_prompt,
            synthesis_prompt_template,
        )

        self._running_jobs[job.id] = future
        future.add_done_callback(lambda f: self._running_jobs.pop(job.id, None))

        return job

    def _run_analysis(
        self,
        job_id: str,
        session_file: Path,
        system_prompt: str,
        analysis_prompt_template: str,
        model: str,
        context_size: int,
        chunk_system_prompt: str | None = None,
        chunk_prompt_template: str | None = None,
        synthesis_system_prompt: str | None = None,
        synthesis_prompt_template: str | None = None,
    ) -> None:
        """
        Execute analysis in background thread.

        Automatically detects if transcript should be chunked based on token count.
        Uses map-reduce pattern for large transcripts when chunk prompts are provided.

        Args:
            job_id: Job ID to update
            session_file: Path to session file
            system_prompt: System prompt (for single-pass)
            analysis_prompt_template: Prompt template with {transcript}
            model: Model to use
            context_size: Context size
            chunk_system_prompt: System prompt for chunk analysis
            chunk_prompt_template: Prompt template for chunks
            synthesis_system_prompt: System prompt for synthesis
            synthesis_prompt_template: Prompt template for synthesis
        """
        try:
            # Mark as running
            self.storage.update_job_status(job_id, JobStatus.RUNNING)

            # Parse messages from session file
            logger.info(f"Job {job_id}: Parsing messages from {session_file}")
            messages = list(parse_session_file(session_file))
            transcript = format_transcript(messages)
            transcript_lines = len(transcript.splitlines())

            # Estimate tokens to decide chunking strategy
            total_tokens = estimate_tokens(transcript)
            chunk_threshold = int(self.chunk_tokens * 0.8)

            # Determine if we should chunk
            should_chunk = (
                total_tokens > chunk_threshold
                and chunk_prompt_template is not None
                and synthesis_prompt_template is not None
            )

            if should_chunk:
                logger.info(
                    f"Job {job_id}: Transcript has ~{total_tokens} tokens "
                    f"(threshold: {chunk_threshold}), using chunked analysis"
                )
                result_text = self._run_chunked(
                    job_id=job_id,
                    messages=messages,
                    model=model,
                    context_size=context_size,
                    chunk_system_prompt=chunk_system_prompt or system_prompt,
                    chunk_prompt_template=chunk_prompt_template,
                    synthesis_system_prompt=synthesis_system_prompt or system_prompt,
                    synthesis_prompt_template=synthesis_prompt_template,
                )
            else:
                if total_tokens <= chunk_threshold:
                    logger.info(
                        f"Job {job_id}: Transcript has ~{total_tokens} tokens "
                        f"(under threshold), using single-pass analysis"
                    )
                else:
                    logger.info(
                        f"Job {job_id}: Transcript exceeds threshold but no chunk "
                        f"prompts provided, using single-pass analysis"
                    )

                # Single-pass analysis (original behavior)
                prompt = analysis_prompt_template.format(transcript=transcript)
                response: GenerateResponse = generate_sync(
                    model=model,
                    prompt=prompt,
                    system=system_prompt,
                    context_size=context_size,
                )
                result_text = response.response

            # Store result
            self.storage.complete_job(
                job_id=job_id,
                result_text=result_text,
                transcript_lines=transcript_lines,
                model_used=model,
                context_size=context_size,
            )
            logger.info(f"Job {job_id}: Completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id}: Failed with error: {e}")
            self.storage.fail_job(job_id, str(e))

    def _run_chunked(
        self,
        job_id: str,
        messages: list[Message],
        model: str,
        context_size: int,
        chunk_system_prompt: str,
        chunk_prompt_template: str,
        synthesis_system_prompt: str,
        synthesis_prompt_template: str,
    ) -> str:
        """
        Run map-reduce chunked analysis.

        Map phase: Analyze each chunk independently
        Reduce phase: Synthesize chunk results into final output

        Args:
            job_id: Job ID for logging
            messages: Parsed messages from transcript
            model: Model to use
            context_size: Context size
            chunk_system_prompt: System prompt for chunk analysis
            chunk_prompt_template: Template with {transcript}, {chunk_index}, {total_chunks}
            synthesis_system_prompt: System prompt for synthesis
            synthesis_prompt_template: Template with {chunk_results}, {total_chunks}

        Returns:
            Synthesized result text
        """
        # Chunk the messages
        chunking_result = chunk_messages(
            messages,
            target_tokens=self.chunk_tokens,
            overlap_turns=self.overlap_turns,
        )

        logger.info(
            f"Job {job_id}: Created {len(chunking_result.chunks)} chunks from "
            f"{chunking_result.total_messages} messages"
        )

        # Map phase: analyze each chunk
        chunk_results: list[str] = []
        for chunk in chunking_result.chunks:
            chunk_transcript = chunk.format_transcript()

            # Format the chunk prompt
            prompt = chunk_prompt_template.format(
                transcript=chunk_transcript,
                chunk_index=chunk.chunk_index + 1,  # 1-indexed for display
                total_chunks=chunk.total_chunks,
            )

            logger.info(
                f"Job {job_id}: Analyzing chunk {chunk.chunk_index + 1}/"
                f"{chunk.total_chunks} (~{chunk.estimated_tokens} tokens)"
            )

            response: GenerateResponse = generate_sync(
                model=model,
                prompt=prompt,
                system=chunk_system_prompt.format(
                    chunk_index=chunk.chunk_index + 1,
                    total_chunks=chunk.total_chunks,
                ),
                context_size=context_size,
            )
            chunk_results.append(
                f"=== Chunk {chunk.chunk_index + 1}/{chunk.total_chunks} ===\n\n"
                f"{response.response}"
            )

        # Reduce phase: synthesize results
        logger.info(f"Job {job_id}: Synthesizing {len(chunk_results)} chunk results")

        synthesis_prompt = synthesis_prompt_template.format(
            chunk_results="\n\n".join(chunk_results),
            total_chunks=len(chunk_results),
        )

        synthesis_response: GenerateResponse = generate_sync(
            model=model,
            prompt=synthesis_prompt,
            system=synthesis_system_prompt,
            context_size=context_size,
        )

        return synthesis_response.response

    def get_job_status(self, job_id: str) -> Job | None:
        """Get current status of a job."""
        return self.storage.get_job(job_id)

    def get_job_result(self, job_id: str) -> str | None:
        """Get result text for a completed job."""
        job = self.storage.get_job(job_id)
        if job is None or job.result_id is None:
            return None

        result = self.storage.get_result(job.result_id)
        return result.result_text if result else None

    def is_job_running(self, job_id: str) -> bool:
        """Check if a job is currently running."""
        return job_id in self._running_jobs

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the thread pool."""
        self._executor.shutdown(wait=wait)
