"""Optional external LLM client for OpenAI-compatible chat APIs."""

from dataclasses import dataclass
import os
from typing import Dict, List, Optional

import httpx

from app.core.config import get_settings


PROVIDER_BASE_URLS = {
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "together": "https://api.together.xyz/v1",
    "siliconflow": "https://api.siliconflow.cn/v1",
    "alibaba": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "openai": "https://api.openai.com/v1",
    "local": "http://127.0.0.1:10531/v1",
}

PROVIDER_KEY_ENV = {
    "nvidia": "NVIDIA_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "together": "TOGETHER_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY",
    "alibaba": "ALIBABA_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "local": "LOCAL_LLM_API_KEY",
}

PROVIDER_DEFAULT_MODELS = {
    "nvidia": "meta/llama-3.3-70b-instruct",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "siliconflow": "Qwen/Qwen2.5-32B-Instruct",
    "alibaba": "qwen-plus",
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o-mini",
    "local": "gpt-5.4",
}

PROVIDER_MODEL_OPTIONS = {
    "nvidia": [
        "meta/llama-3.3-70b-instruct",
        "meta/llama-4-maverick-17b-128e-instruct",
    ],
    "groq": ["llama-3.3-70b-versatile"],
    "siliconflow": ["Qwen/Qwen2.5-32B-Instruct"],
}

PROVIDER_LABELS = {
    "nvidia": "NVIDIA",
    "groq": "Groq",
    "siliconflow": "硅基流动",
}


@dataclass(frozen=True)
class LLMProviderConfig:
    enabled: bool
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float
    max_tokens: int
    temperature: float
    top_p: float

    @property
    def is_configured(self) -> bool:
        if not self.enabled:
            return False
        if not self.base_url or not self.model:
            return False
        if self.provider == "local":
            return True
        return bool(self.api_key)


def get_llm_provider_config(
    provider_override: Optional[str] = None,
    model_override: Optional[str] = None,
) -> LLMProviderConfig:
    settings = get_settings()
    provider = (provider_override or settings.llm_provider or "local").strip().lower()
    if provider not in PROVIDER_BASE_URLS:
        provider = settings.llm_provider or "local"

    api_key_env = PROVIDER_KEY_ENV.get(provider, "LLM_API_KEY")
    configured_key = settings.llm_api_key
    if provider != "local" and configured_key.lower() == "not-needed":
        configured_key = ""
    api_key = configured_key or os.getenv(api_key_env, "").strip()

    if provider == "local" and not api_key:
        api_key = "not-needed"

    base_url = PROVIDER_BASE_URLS.get(provider, "")
    if provider == settings.llm_provider and settings.llm_base_url:
        base_url = settings.llm_base_url

    return LLMProviderConfig(
        enabled=settings.llm_enabled,
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        model=model_override or settings.llm_model or PROVIDER_DEFAULT_MODELS.get(provider, ""),
        timeout_seconds=settings.llm_timeout_seconds,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        top_p=settings.llm_top_p,
    )


def list_llm_model_options() -> Dict:
    settings = get_settings()
    default_config = get_llm_provider_config()
    options = []

    for provider, models in PROVIDER_MODEL_OPTIONS.items():
        provider_config = get_llm_provider_config(provider_override=provider)
        for model in models:
            options.append(
                {
                    "provider": provider,
                    "model": model,
                    "label": "{0} · {1}".format(
                        PROVIDER_LABELS.get(provider, provider),
                        model,
                    ),
                    "configured": provider_config.is_configured,
                }
            )

    return {
        "enabled": settings.llm_enabled,
        "default_provider": default_config.provider,
        "default_model": default_config.model,
        "options": options,
    }


def build_external_assistant_answer(
    question: str,
    local_reply: Dict,
    kb_result: Dict,
    grounding_context_text: str = "",
) -> Optional[Dict[str, str]]:
    """Return an external LLM answer, or None when disabled/unavailable."""
    config = get_llm_provider_config(
        provider_override=local_reply.get("llm_provider"),
        model_override=local_reply.get("llm_model"),
    )
    if not config.is_configured:
        return None

    messages = _build_grounded_messages(question, local_reply, kb_result, grounding_context_text)

    try:
        answer = _chat_completion(config, messages)
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None

    if answer and _is_usable_external_answer(question, answer):
        return {
            "answer": answer,
            "provider": config.provider,
            "model": config.model,
        }
    return None


def _build_grounded_messages(
    question: str,
    local_reply: Dict,
    kb_result: Dict,
    grounding_context_text: str = "",
) -> List[Dict[str, str]]:
    context_lines = []
    for item in kb_result.get("answer_context", [])[:4]:
        context_lines.append(
            "来源：{file}\n章节：{section}\n片段：{snippet}".format(
                file=item.get("file", ""),
                section=item.get("section", ""),
                snippet=item.get("snippet", ""),
            )
        )

    knowledge_context = "\n\n".join(context_lines) or "暂无额外知识库片段。"
    realtime_context = grounding_context_text.strip() or "本问题未匹配到需要强接地的实时工单上下文。"
    citations = "、".join(item.get("path", "") for item in local_reply.get("citations", []))

    system_prompt = (
        "你是建筑能源智能管理系统的运维问答助手。"
        "请使用中文回答，回答必须基于给定数据结论和知识库片段，"
        "不要编造系统中没有的数据。涉及工单时，只能使用 REAL_TIME_WORK_ORDER_CONTEXT "
        "中给出的 work_order_id、equipment_id、状态、时间线、损失和节约数据；"
        "如果上下文没有对应实体，就明确说明当前实时数据未提供。"
        "必须直接回答用户问题，不要泛泛介绍系统能力。"
        "回答控制在 180 字以内，适合课堂演示。"
    )
    user_prompt = (
        "用户问题：{question}\n\n"
        "本地规则分析结论：{local_answer}\n\n"
        "实时业务上下文：\n{realtime_context}\n\n"
        "已匹配知识库片段：\n{knowledge_context}\n\n"
        "已有引用路径：{citations}\n\n"
        "请给出更自然但仍然可追溯的回答。不要说“可以询问”“随时提问”这类空泛话。"
    ).format(
        question=question,
        local_answer=local_reply.get("answer", ""),
        realtime_context=realtime_context,
        knowledge_context=knowledge_context,
        citations=citations,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _chat_completion(config: LLMProviderConfig, messages: List[Dict[str, str]]) -> Optional[str]:
    endpoint = config.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": "Bearer {0}".format(config.api_key),
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_tokens": config.max_tokens,
        "stream": False,
    }

    with httpx.Client(timeout=config.timeout_seconds) as client:
        response = client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"].get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None


def _is_usable_external_answer(question: str, answer: str) -> bool:
    question_text = question.lower()
    answer_text = answer.lower()
    generic_phrases = [
        "可以询问",
        "随时询问",
        "尽力提供",
        "我可以帮助",
        "可以回答",
        "如果您有",
        "可以选择",
    ]
    if any(phrase in answer_text for phrase in generic_phrases):
        return False

    keyword_groups = [
        (["异常"], ["异常", "告警", "设备", "记录"]),
        (["cop", "能效", "制冷效率"], ["cop", "能效", "制冷"]),
        (["维护", "保养", "巡检", "冷却塔"], ["维护", "保养", "巡检", "冷却塔"]),
        (["建筑", "教学楼", "实验楼", "办公楼", "图书"], ["建筑", "教学楼", "实验楼", "办公楼", "图书"]),
        (["数据", "来源", "随机"], ["数据", "来源", "随机", "公开资料", "模拟"]),
    ]
    for question_keywords, required_answer_terms in keyword_groups:
        if any(keyword in question_text for keyword in question_keywords):
            return any(term in answer_text for term in required_answer_terms)

    return len(answer_text.strip()) >= 20
