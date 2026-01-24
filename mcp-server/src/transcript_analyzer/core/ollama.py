"""Async Ollama API client."""

import httpx
from dataclasses import dataclass


@dataclass
class OllamaModel:
    """Information about an Ollama model."""

    name: str
    size: int
    modified_at: str


@dataclass
class GenerateResponse:
    """Response from Ollama generate API."""

    response: str
    model: str
    total_duration: int | None = None
    prompt_eval_count: int | None = None
    eval_count: int | None = None


class OllamaError(Exception):
    """Error from Ollama API."""

    pass


class OllamaClient:
    """Async client for Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: float = 300.0,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
            timeout: Request timeout in seconds (default 5 minutes for long generations)
        """
        self.base_url = base_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        context_size: int = 32768,
    ) -> GenerateResponse:
        """
        Generate text using Ollama.

        Args:
            model: Model name (e.g., "qwen2.5:72b")
            prompt: The prompt text
            system: Optional system prompt
            context_size: Context window size (num_ctx)

        Returns:
            GenerateResponse with the generated text

        Raises:
            OllamaError: If the API call fails
        """
        client = await self._get_client()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_ctx": context_size},
        }

        if system:
            payload["system"] = system

        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

            return GenerateResponse(
                response=data["response"],
                model=data.get("model", model),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count"),
            )
        except httpx.HTTPStatusError as e:
            raise OllamaError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise OllamaError(f"Failed to connect to Ollama: {e}")

    async def list_models(self) -> list[OllamaModel]:
        """
        List available Ollama models.

        Returns:
            List of OllamaModel objects
        """
        client = await self._get_client()

        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            return [
                OllamaModel(
                    name=m["name"],
                    size=m.get("size", 0),
                    modified_at=m.get("modified_at", ""),
                )
                for m in data.get("models", [])
            ]
        except httpx.HTTPStatusError as e:
            raise OllamaError(f"Ollama API error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise OllamaError(f"Failed to connect to Ollama: {e}")

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False


# Synchronous wrapper for use in thread pool
def generate_sync(
    model: str,
    prompt: str,
    system: str | None = None,
    context_size: int = 32768,
    base_url: str = "http://localhost:11434",
    timeout: float = 300.0,
) -> GenerateResponse:
    """
    Synchronous version of generate for use in background threads.

    Args:
        model: Model name
        prompt: The prompt text
        system: Optional system prompt
        context_size: Context window size
        base_url: Ollama API base URL
        timeout: Request timeout in seconds

    Returns:
        GenerateResponse with the generated text
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": context_size},
    }

    if system:
        payload["system"] = system

    try:
        with httpx.Client(base_url=base_url, timeout=timeout) as client:
            response = client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

            return GenerateResponse(
                response=data["response"],
                model=data.get("model", model),
                total_duration=data.get("total_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count"),
            )
    except httpx.HTTPStatusError as e:
        raise OllamaError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        raise OllamaError(f"Failed to connect to Ollama: {e}")
