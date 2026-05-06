"""Tests for the knowledge search service."""

from app.services.knowledge_search_service import (
    search_and_format_citations,
    search_knowledge,
    clear_knowledge_cache,
)


def test_search_knowledge_returns_results():
    results = search_knowledge("建筑能耗", top_k=3)
    assert len(results) > 0


def test_search_knowledge_has_scores():
    results = search_knowledge("异常诊断")
    for r in results:
        assert r.score > 0


def test_search_knowledge_matches_cop():
    results = search_knowledge("COP 能效")
    matched_texts = " ".join(
        r.section.title + " " + r.section.body for r in results
    ).lower()
    assert any(
        kw in matched_texts for kw in ["cop", "能效", "制冷"]
    )


def test_search_knowledge_matches_maintenance():
    results = search_knowledge("冷却塔 维护")
    matched_texts = " ".join(
        r.section.body for r in results
    ).lower()
    assert any(
        kw in matched_texts for kw in ["维护", "冷却塔", "巡检"]
    )


def test_search_and_format_citations_returns_structure():
    result = search_and_format_citations("COP 排名")
    assert "citations" in result
    assert "answer_context" in result
    assert "match_summary" in result
    assert len(result["citations"]) > 0
    assert len(result["answer_context"]) > 0


def test_search_and_format_citations_empty_query():
    result = search_and_format_citations("")
    assert result["citations"] == []
    assert "未能在知识库中" in result["match_summary"] or result["answer_context"] == []


def test_clear_knowledge_cache():
    results_before = search_knowledge("设备")
    clear_knowledge_cache()
    results_after = search_knowledge("设备")
    assert len(results_before) == len(results_after)
