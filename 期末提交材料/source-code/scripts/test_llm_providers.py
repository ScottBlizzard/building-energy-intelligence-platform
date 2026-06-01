"""Smoke-test configured LLM providers from the local .env file.

This script never prints API keys. It sends a tiny prompt to each configured
provider/model and reports whether the call succeeds.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List

import httpx
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)


PROVIDERS: Dict[str, Dict[str, object]] = {
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env": "NVIDIA_API_KEY",
        "models": [
            "meta/llama-3.3-70b-instruct",
            "meta/llama-4-maverick-17b-128e-instruct",
        ],
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "models": ["llama-3.3-70b-versatile"],
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "models": ["meta-llama/llama-3.3-70b-instruct"],
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "key_env": "TOGETHER_API_KEY",
        "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo"],
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "key_env": "SILICONFLOW_API_KEY",
        "models": ["Qwen/Qwen2.5-32B-Instruct"],
    },
    "alibaba": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "key_env": "ALIBABA_API_KEY",
        "models": ["qwen-plus"],
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "models": ["gemini-2.0-flash"],
    },
    "local": {
        "base_url": os.getenv("LLM_BASE_URL") or "http://127.0.0.1:10531/v1",
        "key_env": "LOCAL_LLM_API_KEY",
        "models": [os.getenv("LOCAL_LLM_MODEL", "gpt-5.4")],
    },
}


def enabled_provider_names() -> List[str]:
    raw = os.getenv("LLM_TEST_PROVIDERS", "").strip()
    if not raw:
        return list(PROVIDERS.keys())
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def provider_key(provider: str, key_env: str) -> str:
    if provider == "local":
        return os.getenv(key_env) or os.getenv("LLM_API_KEY") or "not-needed"
    return os.getenv(key_env, "").strip()


def iter_checks() -> Iterable[tuple[str, str, str, str]]:
    for provider in enabled_provider_names():
        config = PROVIDERS.get(provider)
        if not config:
            yield provider, "", "SKIP", "unknown provider"
            continue

        key = provider_key(provider, str(config["key_env"]))
        if not key or key.startswith("replace_with"):
            yield provider, "", "SKIP", "missing API key"
            continue

        for model in config["models"]:
            yield provider, str(model), key, str(config["base_url"])


def test_model(provider: str, model: str, api_key: str, base_url: str) -> tuple[str, str]:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请只回复 OK"}],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 8,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(endpoint, headers=headers, json=payload)
        if response.status_code >= 400:
            return "FAIL", f"HTTP {response.status_code}: {response.text[:180]}"
        data = response.json()
        content = data["choices"][0]["message"].get("content", "").strip()
        return "OK", content[:80] or "(empty content)"
    except Exception as exc:  # noqa: BLE001 - smoke test should keep running.
        return "FAIL", f"{type(exc).__name__}: {exc}"


def main() -> int:
    print("LLM provider smoke test")
    print("Keys are loaded from .env and are never printed.\n")

    has_failure = False
    for provider, model, key_or_status, base_url_or_reason in iter_checks():
        if key_or_status == "SKIP":
            print(f"[SKIP] {provider}: {base_url_or_reason}")
            continue

        status, detail = test_model(provider, model, key_or_status, base_url_or_reason)
        if status != "OK":
            has_failure = True
        print(f"[{status}] {provider} | {model} | {detail}")

    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
