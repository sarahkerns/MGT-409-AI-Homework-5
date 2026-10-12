import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(WORKSPACE_ROOT / ".env")


def luna_model() -> OpenAIChatModel:
    """Create the sole permitted agent model through Portkey."""
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is required")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"},
    )
    provider = OpenAIProvider(openai_client=client)
    return OpenAIChatModel("gpt-6-luna", provider=provider)
