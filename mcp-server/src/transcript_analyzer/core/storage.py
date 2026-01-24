"""SQLite storage for jobs and analysis results."""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterator
from uuid import uuid4


class JobStatus(Enum):
    """Status of an analysis job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(Enum):
    """Type of analysis job."""

    STENOGRAPHER = "stenographer"
    INSIGHT_EXTRACTOR = "insight_extractor"


@dataclass
class Job:
    """An analysis job."""

    id: str
    type: JobType
    session_id: str
    project_path: str | None
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
    result_id: str | None = None


@dataclass
class AnalysisResult:
    """Result of an analysis job."""

    id: str
    type: JobType
    session_id: str
    project_path: str | None
    transcript_lines: int
    model_used: str
    context_size: int
    result_text: str
    created_at: datetime


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    session_id TEXT NOT NULL,
    project_path TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error_message TEXT,
    result_id TEXT,
    FOREIGN KEY (result_id) REFERENCES analysis_results(id)
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    session_id TEXT NOT NULL,
    project_path TEXT,
    transcript_lines INTEGER,
    model_used TEXT,
    context_size INTEGER,
    result_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_session ON jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_results_session ON analysis_results(session_id);
"""


class Storage:
    """SQLite storage for jobs and results."""

    def __init__(self, db_path: Path | None = None):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.claude/transcript-analyzer/data.db
        """
        if db_path is None:
            db_path = Path.home() / ".claude" / "transcript-analyzer" / "data.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_job(
        self,
        job_type: JobType,
        session_id: str,
        project_path: str | None = None,
    ) -> Job:
        """Create a new pending job."""
        job_id = str(uuid4())
        now = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, type, session_id, project_path, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (job_id, job_type.value, session_id, project_path, JobStatus.PENDING.value, now, now),
            )

        return Job(
            id=job_id,
            type=job_type,
            session_id=session_id,
            project_path=project_path,
            status=JobStatus.PENDING,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

        if row is None:
            return None

        return Job(
            id=row["id"],
            type=JobType(row["type"]),
            session_id=row["session_id"],
            project_path=row["project_path"],
            status=JobStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            error_message=row["error_message"],
            result_id=row["result_id"],
        )

    def update_job_status(self, job_id: str, status: JobStatus) -> None:
        """Update job status."""
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, job_id),
            )

    def fail_job(self, job_id: str, error_message: str) -> None:
        """Mark job as failed with error message."""
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                (JobStatus.FAILED.value, error_message, now, job_id),
            )

    def complete_job(
        self,
        job_id: str,
        result_text: str,
        transcript_lines: int,
        model_used: str,
        context_size: int,
    ) -> AnalysisResult:
        """Mark job as completed and store result."""
        result_id = str(uuid4())
        now = datetime.now().isoformat()

        # Get job info for result
        job = self.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        with self._connect() as conn:
            # Store result
            conn.execute(
                """
                INSERT INTO analysis_results
                (id, type, session_id, project_path, transcript_lines, model_used, context_size, result_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    job.type.value,
                    job.session_id,
                    job.project_path,
                    transcript_lines,
                    model_used,
                    context_size,
                    result_text,
                    now,
                ),
            )

            # Update job
            conn.execute(
                "UPDATE jobs SET status = ?, result_id = ?, updated_at = ? WHERE id = ?",
                (JobStatus.COMPLETED.value, result_id, now, job_id),
            )

        return AnalysisResult(
            id=result_id,
            type=job.type,
            session_id=job.session_id,
            project_path=job.project_path,
            transcript_lines=transcript_lines,
            model_used=model_used,
            context_size=context_size,
            result_text=result_text,
            created_at=datetime.fromisoformat(now),
        )

    def get_result(self, result_id: str) -> AnalysisResult | None:
        """Get an analysis result by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM analysis_results WHERE id = ?", (result_id,)
            ).fetchone()

        if row is None:
            return None

        return AnalysisResult(
            id=row["id"],
            type=JobType(row["type"]),
            session_id=row["session_id"],
            project_path=row["project_path"],
            transcript_lines=row["transcript_lines"],
            model_used=row["model_used"],
            context_size=row["context_size"],
            result_text=row["result_text"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def list_jobs(
        self,
        status: JobStatus | None = None,
        session_id: str | None = None,
        job_type: JobType | None = None,
        limit: int = 20,
    ) -> list[Job]:
        """List jobs with optional filtering."""
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if job_type:
            query += " AND type = ?"
            params.append(job_type.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Job(
                id=row["id"],
                type=JobType(row["type"]),
                session_id=row["session_id"],
                project_path=row["project_path"],
                status=JobStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                error_message=row["error_message"],
                result_id=row["result_id"],
            )
            for row in rows
        ]

    def cleanup_old_results(self, days: int = 30) -> int:
        """Delete results older than specified days. Returns count deleted."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()

        with self._connect() as conn:
            # Delete old results
            cursor = conn.execute(
                "DELETE FROM analysis_results WHERE created_at < ?", (cutoff_iso,)
            )
            deleted = cursor.rowcount

            # Delete orphaned jobs (result deleted)
            conn.execute(
                """
                DELETE FROM jobs
                WHERE result_id IS NOT NULL
                AND result_id NOT IN (SELECT id FROM analysis_results)
                """
            )

        return deleted
