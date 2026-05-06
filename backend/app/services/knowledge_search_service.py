"""Simple keyword-based knowledge search over local knowledge_base markdown files.

Does NOT modify any knowledge_base files.  Reads them read-only and builds
an in-memory index of sections for citation-aware retrieval.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import get_settings


class KnowledgeSection:
    """A single section extracted from a knowledge_base markdown file."""

    def __init__(self, title: str, body: str, file_path: str, section_index: int):
        self.title = title
        self.body = body
        self.file_path = file_path
        self.section_index = section_index


class SearchResult:
    """A ranked search result."""

    def __init__(self, section: KnowledgeSection, score: int, matched_keywords: List[str]):
        self.section = section
        self.score = score
        self.matched_keywords = matched_keywords


@lru_cache(maxsize=1)
def _load_knowledge_sections() -> List[KnowledgeSection]:
    """Load all knowledge_base .md files and split them into sections."""
    settings = get_settings()
    kb_dir = settings.knowledge_base_dir
    if not kb_dir.exists():
        return []

    sections: List[KnowledgeSection] = []
    for md_file in sorted(kb_dir.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        file_sections = _parse_sections(content, str(md_file.relative_to(settings.root_dir)))
        sections.extend(file_sections)

    return sections


def _parse_sections(content: str, rel_path: str) -> List[KnowledgeSection]:
    """Split markdown content into sections by ## headers."""
    sections: List[KnowledgeSection] = []
    # Split on ## headers (but not # which is the document title)
    parts = re.split(r"\n(?=## )", content)

    idx = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        header = lines[0].lstrip("#").strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        if header and body:
            sections.append(KnowledgeSection(
                title=header,
                body=body,
                file_path=rel_path,
                section_index=idx,
            ))
            idx += 1

    return sections


def _tokenize(text: str) -> List[str]:
    """Simple Chinese+English tokenizer: split on whitespace and punctuation."""
    tokens = re.findall(r"[一-鿿]+|[a-zA-Z0-9]+", text.lower())
    return list(set(tokens))


def search_knowledge(
    query: str,
    top_k: int = 5,
) -> List[SearchResult]:
    """Search knowledge base sections for the given query.

    Returns ranked results with matched sections and their source file paths.
    """
    sections = _load_knowledge_sections()
    if not sections:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results: List[SearchResult] = []
    for section in sections:
        body_lower = section.body.lower()
        title_lower = section.title.lower()
        matched: List[str] = []

        for token in query_tokens:
            if token in title_lower:
                matched.append(token)
            elif token in body_lower:
                matched.append(token)

        if matched:
            # Score: title matches count double, plus unique matched tokens
            title_matches = sum(1 for t in matched if t in title_lower)
            score = len(set(matched)) + title_matches
            results.append(SearchResult(
                section=section,
                score=score,
                matched_keywords=list(set(matched)),
            ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]


def search_and_format_citations(
    question: str,
    top_k: int = 3,
) -> Dict:
    """Search knowledge base and return a dict with answer context and citations.

    Returns:
        dict with keys:
        - answer_context: list of (section_title, snippet, file_path) tuples
        - citations: list of {title, path} dicts
        - match_summary: string describing what was found
    """
    results = search_knowledge(question, top_k=top_k)

    citations = []
    answer_context = []
    seen_files = set()

    for r in results:
        if r.section.file_path not in seen_files:
            seen_files.add(r.section.file_path)
            citations.append({
                "title": _extract_doc_title(r.section.file_path) or r.section.title,
                "path": r.section.file_path,
            })
        snippet = r.section.body[:200] + ("..." if len(r.section.body) > 200 else "")
        answer_context.append({
            "section": r.section.title,
            "snippet": snippet,
            "file": r.section.file_path,
        })

    if citations:
        match_summary = "从知识库中匹配到 {0} 个相关片段，关键词：{1}".format(
            len(answer_context),
            "、".join(sorted(set(kw for r in results for kw in r.matched_keywords)))[:60],
        )
    else:
        match_summary = "未能在知识库中找到与问题直接匹配的内容。"

    return {
        "answer_context": answer_context,
        "citations": citations,
        "match_summary": match_summary,
    }


@lru_cache(maxsize=1)
def _get_doc_title_map() -> Dict[str, str]:
    """Build a mapping from relative path to document title (first # heading)."""
    settings = get_settings()
    kb_dir = settings.knowledge_base_dir
    title_map: Dict[str, str] = {}
    if not kb_dir.exists():
        return title_map

    for md_file in kb_dir.rglob("*.md"):
        rel_path = str(md_file.relative_to(settings.root_dir))
        try:
            first_line = md_file.read_text(encoding="utf-8").split("\n")[0].strip()
            if first_line.startswith("# "):
                title_map[rel_path] = first_line[2:].strip()
        except (OSError, UnicodeDecodeError):
            continue
    return title_map


def _extract_doc_title(rel_path: str) -> Optional[str]:
    """Get the document title for a knowledge_base file."""
    return _get_doc_title_map().get(rel_path)


def clear_knowledge_cache() -> None:
    """Clear all cached knowledge indices."""
    _load_knowledge_sections.cache_clear()
    _get_doc_title_map.cache_clear()
