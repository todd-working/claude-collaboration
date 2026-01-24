# Transcript Analyzer

MCP server for Claude Code session transcript analysis.

## Features

- List and search Claude Code sessions
- Extract readable transcripts
- Run stenographer analysis (structured state extraction)
- Run insight extraction (training signal generation)
- Background job support for long-running analysis

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

### As MCP Server

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "transcript-analyzer": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "transcript_analyzer.server"],
      "cwd": "/path/to/mcp-server"
    }
  }
}
```

### Available Tools

- `list_sessions` - Find Claude Code sessions by project/date
- `extract_transcript` - Get readable transcript from session
- `run_stenographer` - Extract structured state (async)
- `run_insight_extractor` - Deep analysis for training signal (async)
- `get_job_status` - Check status of async jobs
- `list_jobs` - Query job history
- `list_models` - List available Ollama models

## Configuration

Environment variables:
- `TRANSCRIPT_ANALYZER_MODEL` - Default Ollama model (default: `qwen2.5:72b`)
- `TRANSCRIPT_ANALYZER_CTX` - Default context size (default: `32768`)
- `OLLAMA_URL` - Ollama API URL (default: `http://localhost:11434`)

## Development

```bash
# Run tests
pytest tests/

# Run linter
ruff check src/
```
