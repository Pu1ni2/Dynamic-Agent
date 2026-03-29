import json
from openai import OpenAI
from .config import API_KEY, BASE_URL

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return _client


def call_llm(model: str, messages: list, max_tokens: int = 2048) -> str:
    response = get_client().chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def call_llm_json(model: str, messages: list, max_tokens: int = 2048) -> dict:
    raw = call_llm(model, messages, max_tokens=max_tokens)
    # Strip markdown code fences if the model wraps the JSON
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(stripped)
