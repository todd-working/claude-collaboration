"""Background job manager for analysis tasks."""

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from .ollama import GenerateResponse, generate_sync
from .parser import extract_transcript
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
    ):
        """
        Initialize job manager.

        Args:
            storage: Storage instance for jobs and results
            max_workers: Maximum concurrent analysis jobs
            default_model: Default Ollama model to use
            default_context_size: Default context window size
        """
        self.storage = storage
        self.default_model = default_model
        self.default_context_size = default_context_size
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
    ) -> Job:
        """
        Submit an analysis job for background execution.

        Args:
            job_type: Type of analysis (stenographer or insight_extractor)
            session_file: Path to the session JSONL file
            system_prompt: System prompt for the model
            analysis_prompt_template: Prompt template with {transcript} placeholder
            model: Ollama model to use (defaults to default_model)
            context_size: Context window size (defaults to default_context_size)

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
    ) -> None:
        """
        Execute analysis in background thread.

        Args:
            job_id: Job ID to update
            session_file: Path to session file
            system_prompt: System prompt
            analysis_prompt_template: Prompt template with {transcript}
            model: Model to use
            context_size: Context size
        """
        try:
            # Mark as running
            self.storage.update_job_status(job_id, JobStatus.RUNNING)

            # Extract transcript
            logger.info(f"Job {job_id}: Extracting transcript from {session_file}")
            transcript = extract_transcript(session_file)
            transcript_lines = len(transcript.splitlines())

            # Build prompt with transcript
            prompt = analysis_prompt_template.format(transcript=transcript)

            # Call Ollama
            logger.info(f"Job {job_id}: Calling Ollama ({model}, ctx={context_size})")
            response: GenerateResponse = generate_sync(
                model=model,
                prompt=prompt,
                system=system_prompt,
                context_size=context_size,
            )

            # Store result
            self.storage.complete_job(
                job_id=job_id,
                result_text=response.response,
                transcript_lines=transcript_lines,
                model_used=model,
                context_size=context_size,
            )
            logger.info(f"Job {job_id}: Completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id}: Failed with error: {e}")
            self.storage.fail_job(job_id, str(e))

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
