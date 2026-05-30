from app.core.config import get_settings
from app.services.llm_client import (
    get_llm_provider_config,
    build_external_assistant_answer,
    _is_usable_external_answer,
)


def _reset_settings():
    get_settings.cache_clear()


def test_llm_client_disabled_by_default(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    _reset_settings()

    result = build_external_assistant_answer(
        "当前有哪些异常？",
        {"answer": "本地回答", "citations": []},
        {"answer_context": []},
    )

    assert result is None
    _reset_settings()


def test_llm_provider_uses_provider_specific_key(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("LLM_MODEL", "meta/llama-3.3-70b-instruct")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_API_KEY", "test-secret")
    _reset_settings()

    config = get_llm_provider_config()

    assert config.is_configured
    assert config.provider == "nvidia"
    assert config.api_key == "test-secret"
    assert config.base_url == "https://integrate.api.nvidia.com/v1"
    _reset_settings()


def test_local_provider_does_not_require_real_key(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LOCAL_LLM_API_KEY", raising=False)
    _reset_settings()

    config = get_llm_provider_config()

    assert config.is_configured
    assert config.api_key == "not-needed"
    assert config.base_url == "http://127.0.0.1:10531/v1"
    _reset_settings()


def test_external_provider_ignores_not_needed_placeholder(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_API_KEY", "not-needed")
    monkeypatch.setenv("GROQ_API_KEY", "real-provider-key")
    _reset_settings()

    config = get_llm_provider_config()

    assert config.api_key == "real-provider-key"
    assert config.is_configured
    _reset_settings()


def test_external_answer_quality_gate_rejects_generic_reply():
    assert not _is_usable_external_answer(
        "当前样例数据有哪些异常记录？",
        "您好，系统可以回答数据来源、能耗概况、COP 和异常诊断问题。",
    )


def test_external_answer_quality_gate_accepts_relevant_reply():
    assert _is_usable_external_answer(
        "当前样例数据有哪些异常记录？",
        "当前样例数据存在多条异常记录，主要涉及设备状态异常和非工作时段高能耗。",
    )
