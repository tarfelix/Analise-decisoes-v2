"""Multi-provider LLM service (pattern from sp-zion-automacao/llm_analyzer.py).

Supports: Anthropic Claude, OpenAI, Google Gemini.
Routing by model name prefix.
"""

import json
import logging
import time
from collections.abc import AsyncGenerator

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_provider(model: str) -> str:
    """Detect LLM provider from model name."""
    if model.startswith("claude"):
        return "anthropic"
    elif model.startswith("gemini"):
        return "gemini"
    return "openai"


async def chat_completion(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> dict:
    """Single-shot LLM call. Returns parsed response.

    Returns:
        dict with keys: content, model, tokens_input, tokens_output, duration_ms
    """
    model = model or settings.anthropic_model
    provider = _get_provider(model)
    start = time.time()

    if provider == "anthropic":
        result = await _call_anthropic(system_prompt, user_message, model, temperature)
    elif provider == "gemini":
        result = await _call_gemini(system_prompt, user_message, model, temperature)
    else:
        result = await _call_openai(system_prompt, user_message, model, temperature, json_mode)

    result["duration_ms"] = int((time.time() - start) * 1000)
    result["model"] = model

    # Try to parse JSON from response
    if json_mode or "```json" in result.get("content", ""):
        try:
            content = result["content"]
            # Strip markdown fences
            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in content:
                content = content.split("```", 1)[1].split("```", 1)[0]
            result["parsed"] = json.loads(content.strip())
        except (json.JSONDecodeError, IndexError):
            result["parsed"] = None

    return result


async def stream_completion(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.3,
) -> AsyncGenerator[str, None]:
    """Stream LLM response as SSE events.

    Yields text chunks as they arrive.
    """
    model = model or settings.anthropic_model
    provider = _get_provider(model)

    if provider == "anthropic":
        async for chunk in _stream_anthropic(system_prompt, user_message, model, temperature):
            yield chunk
    elif provider == "openai":
        async for chunk in _stream_openai(system_prompt, user_message, model, temperature):
            yield chunk
    else:
        # Gemini: fall back to non-streaming
        result = await _call_gemini(system_prompt, user_message, model, temperature)
        yield result.get("content", "")


# --- Provider implementations ---


async def _call_anthropic(
    system: str, user: str, model: str, temperature: float
) -> dict:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    return {
        "content": response.content[0].text,
        "tokens_input": response.usage.input_tokens,
        "tokens_output": response.usage.output_tokens,
    }


async def _stream_anthropic(
    system: str, user: str, model: str, temperature: float
) -> AsyncGenerator[str, None]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    async with client.messages.stream(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _call_openai(
    system: str, user: str, model: str, temperature: float, json_mode: bool = False
) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    kwargs = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    choice = response.choices[0]
    return {
        "content": choice.message.content,
        "tokens_input": response.usage.prompt_tokens,
        "tokens_output": response.usage.completion_tokens,
    }


async def _stream_openai(
    system: str, user: str, model: str, temperature: float
) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    stream = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


async def _call_gemini(
    system: str, user: str, model: str, temperature: float
) -> dict:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=model,
        contents=f"{system}\n\n{user}",
        config={"temperature": temperature, "max_output_tokens": 4096},
    )
    return {
        "content": response.text,
        "tokens_input": getattr(response.usage_metadata, "prompt_token_count", 0),
        "tokens_output": getattr(response.usage_metadata, "candidates_token_count", 0),
    }
