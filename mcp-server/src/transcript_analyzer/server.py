"""MCP server for transcript analysis."""

import logging
import os
from pathlib import Path

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .core.job_manager import JobManager
from .core.ollama import OllamaClient
from .core.parser import extract_transcript, find_sessions, get_session_metadata
from .core.storage import JobStatus, JobType, Storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances (initialized on startup)
storage: Storage | None = None
job_manager: JobManager | None = None
ollama_client: OllamaClient | None = None
prompts: dict = {}

# Runtime-configurable settings (persist for session, no restart needed)
runtime_config: dict = {
    "model": None,  # None = use env default
}


def load_prompts(prompts_dir: Path) -> dict:
    """Load prompt templates from YAML files."""
    loaded = {}
    if prompts_dir.exists():
        for yaml_file in prompts_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                loaded[data["name"]] = data
    return loaded


def get_config() -> dict:
    """Get configuration from environment or defaults."""
    return {
        "default_model": os.environ.get("TRANSCRIPT_ANALYZER_MODEL", "qwen2.5:72b"),
        "default_context_size": int(os.environ.get("TRANSCRIPT_ANALYZER_CTX", "32768")),
        "ollama_url": os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        "ollama_timeout": float(os.environ.get("OLLAMA_TIMEOUT", "300")),
        "sessions_dir": os.environ.get(
            "CLAUDE_SESSIONS_DIR", str(Path.home() / ".claude" / "projects")
        ),
        "job_retention_days": int(os.environ.get("JOB_RETENTION_DAYS", "30")),
    }


def get_effective_model(config: dict, request_model: str | None = None) -> str:
    """Get the model to use, with priority: request > runtime > env default."""
    if request_model:
        return request_model
    if runtime_config["model"]:
        return runtime_config["model"]
    return config["default_model"]


# Create server instance
server = Server("transcript-analyzer")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="list_sessions",
            description="List Claude Code sessions, optionally filtered by project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_filter": {
                        "type": "string",
                        "description": "Filter sessions by project path substring",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Only include sessions from last N days (default: 30)",
                        "default": 30,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum sessions to return (default: 20)",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="extract_transcript",
            description="Extract readable transcript from a Claude Code session file",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_file": {
                        "type": "string",
                        "description": "Path to the session .jsonl file",
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include timestamps in output",
                        "default": False,
                    },
                },
                "required": ["session_file"],
            },
        ),
        Tool(
            name="run_stenographer",
            description="Run stenographer analysis to extract structured state from a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_file": {
                        "type": "string",
                        "description": "Path to the session .jsonl file",
                    },
                    "model": {
                        "type": "string",
                        "description": "Ollama model to use (default: qwen2.5:72b)",
                    },
                    "blocking": {
                        "type": "boolean",
                        "description": "Wait for completion (default: false, returns job_id)",
                        "default": False,
                    },
                },
                "required": ["session_file"],
            },
        ),
        Tool(
            name="run_insight_extractor",
            description="Run deep insight extraction on a session for training signal",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_file": {
                        "type": "string",
                        "description": "Path to the session .jsonl file",
                    },
                    "model": {
                        "type": "string",
                        "description": "Ollama model to use (default: qwen2.5:72b)",
                    },
                    "blocking": {
                        "type": "boolean",
                        "description": "Wait for completion (default: false, returns job_id)",
                        "default": False,
                    },
                },
                "required": ["session_file"],
            },
        ),
        Tool(
            name="get_job_status",
            description="Get status and result of an analysis job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID returned by run_stenographer or run_insight_extractor",
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="list_jobs",
            description="List analysis jobs with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["PENDING", "RUNNING", "COMPLETED", "FAILED"],
                        "description": "Filter by job status",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Filter by session ID",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum jobs to return (default: 20)",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="list_models",
            description="List available Ollama models",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="set_model",
            description="Set the default model for analysis (persists until server restart)",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name (e.g., 'qwen2.5:14b', 'mistral:7b'). Use 'default' to reset to env default.",
                    },
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="get_config",
            description="Get current configuration (model, timeout, paths)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    global storage, job_manager, ollama_client, prompts

    config = get_config()

    # Initialize on first call
    if storage is None:
        storage = Storage()
        # Clean up old jobs on startup
        deleted = storage.cleanup_old_results(days=config["job_retention_days"])
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old analysis results")
    if job_manager is None:
        job_manager = JobManager(
            storage,
            default_model=config["default_model"],
            default_context_size=config["default_context_size"],
        )
    if ollama_client is None:
        ollama_client = OllamaClient(
            base_url=config["ollama_url"],
            timeout=config["ollama_timeout"],
        )
    if not prompts:
        # Look for prompts in package directory or parent
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        if not prompts_dir.exists():
            prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
        prompts.update(load_prompts(prompts_dir))

    try:
        if name == "list_sessions":
            sessions = find_sessions(
                base_path=Path(config["sessions_dir"]),
                project_filter=arguments.get("project_filter"),
                days=arguments.get("days", 30),
                limit=arguments.get("limit", 20),
            )
            result = []
            for s in sessions:
                result.append(
                    f"- {s.session_id}\n"
                    f"  Project: {s.project_path or 'unknown'}\n"
                    f"  Modified: {s.modified_at.isoformat()}\n"
                    f"  Size: {s.size_bytes:,} bytes\n"
                    f"  Path: {s.file_path}"
                )
            return [TextContent(type="text", text="\n".join(result) if result else "No sessions found")]

        elif name == "extract_transcript":
            session_file = Path(arguments["session_file"]).expanduser()
            if not session_file.exists():
                return [TextContent(type="text", text=f"Error: File not found: {session_file}")]

            transcript = extract_transcript(
                session_file,
                include_metadata=arguments.get("include_metadata", False),
            )
            return [TextContent(type="text", text=transcript)]

        elif name == "run_stenographer":
            session_file = Path(arguments["session_file"]).expanduser()
            if not session_file.exists():
                return [TextContent(type="text", text=f"Error: File not found: {session_file}")]

            prompt_config = prompts.get("stenographer", {})
            system_prompt = prompt_config.get("system", "")
            prompt_template = prompt_config.get("prompt", "{transcript}")

            model = get_effective_model(config, arguments.get("model"))

            if arguments.get("blocking", False):
                # Blocking mode - wait for result
                transcript = extract_transcript(session_file)
                prompt = prompt_template.format(transcript=transcript)
                response = await ollama_client.generate(
                    model=model,
                    prompt=prompt,
                    system=system_prompt,
                    context_size=config["default_context_size"],
                )
                return [TextContent(type="text", text=response.response)]
            else:
                # Non-blocking - return job ID
                job = job_manager.submit_analysis(
                    job_type=JobType.STENOGRAPHER,
                    session_file=session_file,
                    system_prompt=system_prompt,
                    analysis_prompt_template=prompt_template,
                    model=model,
                )
                return [TextContent(
                    type="text",
                    text=f"Job submitted: {job.id}\nStatus: {job.status.value}\nUse get_job_status to check progress.",
                )]

        elif name == "run_insight_extractor":
            session_file = Path(arguments["session_file"]).expanduser()
            if not session_file.exists():
                return [TextContent(type="text", text=f"Error: File not found: {session_file}")]

            prompt_config = prompts.get("insight_extractor", {})
            system_prompt = prompt_config.get("system", "")
            prompt_template = prompt_config.get("prompt", "{transcript}")

            model = get_effective_model(config, arguments.get("model"))

            if arguments.get("blocking", False):
                # Blocking mode - wait for result
                transcript = extract_transcript(session_file)
                prompt = prompt_template.format(transcript=transcript)
                response = await ollama_client.generate(
                    model=model,
                    prompt=prompt,
                    system=system_prompt,
                    context_size=config["default_context_size"],
                )
                return [TextContent(type="text", text=response.response)]
            else:
                # Non-blocking - return job ID
                job = job_manager.submit_analysis(
                    job_type=JobType.INSIGHT_EXTRACTOR,
                    session_file=session_file,
                    system_prompt=system_prompt,
                    analysis_prompt_template=prompt_template,
                    model=model,
                )
                return [TextContent(
                    type="text",
                    text=f"Job submitted: {job.id}\nStatus: {job.status.value}\nUse get_job_status to check progress.",
                )]

        elif name == "get_job_status":
            job_id = arguments["job_id"]
            job = job_manager.get_job_status(job_id)

            if job is None:
                return [TextContent(type="text", text=f"Job not found: {job_id}")]

            result = [
                f"Job ID: {job.id}",
                f"Type: {job.type.value}",
                f"Session: {job.session_id}",
                f"Status: {job.status.value}",
                f"Created: {job.created_at.isoformat()}",
                f"Updated: {job.updated_at.isoformat()}",
            ]

            if job.status == JobStatus.FAILED:
                result.append(f"Error: {job.error_message}")
            elif job.status == JobStatus.COMPLETED:
                job_result = job_manager.get_job_result(job_id)
                if job_result:
                    result.append("\n--- Result ---\n")
                    result.append(job_result)

            return [TextContent(type="text", text="\n".join(result))]

        elif name == "list_jobs":
            status_filter = None
            if arguments.get("status"):
                status_filter = JobStatus(arguments["status"])

            jobs = storage.list_jobs(
                status=status_filter,
                session_id=arguments.get("session_id"),
                limit=arguments.get("limit", 20),
            )

            if not jobs:
                return [TextContent(type="text", text="No jobs found")]

            result = []
            for job in jobs:
                result.append(
                    f"- {job.id}\n"
                    f"  Type: {job.type.value}\n"
                    f"  Session: {job.session_id}\n"
                    f"  Status: {job.status.value}\n"
                    f"  Created: {job.created_at.isoformat()}"
                )
            return [TextContent(type="text", text="\n".join(result))]

        elif name == "list_models":
            models = await ollama_client.list_models()
            if not models:
                return [TextContent(type="text", text="No models found (is Ollama running?)")]

            current_model = get_effective_model(config)
            result = []
            for model in models:
                size_gb = model.size / (1024 ** 3)
                marker = " ← current" if model.name == current_model else ""
                result.append(f"- {model.name} ({size_gb:.1f} GB){marker}")
            return [TextContent(type="text", text="\n".join(result))]

        elif name == "set_model":
            model = arguments["model"]
            if model.lower() == "default":
                runtime_config["model"] = None
                return [TextContent(type="text", text=f"Model reset to env default: {config['default_model']}")]
            else:
                runtime_config["model"] = model
                return [TextContent(type="text", text=f"Model set to: {model}")]

        elif name == "get_config":
            effective_model = get_effective_model(config)
            result = [
                "**Current Configuration**",
                f"- Model: {effective_model}" + (" (runtime override)" if runtime_config["model"] else " (env default)"),
                f"- Context size: {config['default_context_size']:,}",
                f"- Ollama URL: {config['ollama_url']}",
                f"- Timeout: {config['ollama_timeout']}s",
                f"- Sessions dir: {config['sessions_dir']}",
                f"- Job retention: {config['job_retention_days']} days",
            ]
            return [TextContent(type="text", text="\n".join(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [TextContent(type="text", text=f"Error: {e}")]


async def main():
    """Run the MCP server."""
    logger.info("Starting transcript-analyzer MCP server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
