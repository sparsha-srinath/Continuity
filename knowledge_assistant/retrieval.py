"""Lexical ranking and bounded passages; no domain-specific answer rules."""

import math
import re
from collections import Counter
from pathlib import Path

from .models import SourceChunk
from .chunking import split_source


STOP_WORDS = set("""a an and are as at be been between by can could did do does for from
has have how i in into is it me not of on only or should than that the their them then
there these they this to was were what when where which why will with would you your
changed change compare comparison difference differences legacy modernized modernization
system systems""".split())


def terms(text: str) -> list[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text).lower()
    result = []
    for token in re.findall(r"[a-z0-9]+", text):
        if token in STOP_WORDS:
            continue
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us")):
            token = token[:-1]
        result.append(token)
    return result


def split_chunks(chunks: list[SourceChunk], max_chars: int = 1800) -> list[SourceChunk]:
    """Split by source structure with stable IDs and a strict character bound."""
    if not isinstance(max_chars, int) or max_chars < 1:
        raise ValueError("Maximum chunk characters must be a positive integer.")
    return [part for chunk in chunks if chunk.text.strip() for part in split_source(chunk, max_chars)]


def rank_chunks(query: str, chunks: list[SourceChunk], vector_ids: list[str]) -> list[tuple[SourceChunk, float]]:
    """BM25 over source content and short metadata, with a small vector tie-breaker."""
    query_terms = set(terms(query))
    if not query_terms or not chunks:
        return []
    documents = [Counter(terms(
        f"{chunk.section_title} {Path(chunk.source_file).name} {chunk.entity} {chunk.text}"
    )) for chunk in chunks]
    frequencies = Counter(term for doc in documents for term in doc)
    average_length = sum(sum(doc.values()) for doc in documents) / len(documents) or 1
    vector_ranks = {chunk_id: rank for rank, chunk_id in enumerate(vector_ids)}
    ranked = []
    for chunk, doc in zip(chunks, documents):
        if len(query_terms & doc.keys()) < min(2, len(query_terms)):
            continue
        score = 0.0
        for term in query_terms & doc.keys():
            idf = math.log(1 + (len(documents) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
            tf = doc[term]
            score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * sum(doc.values()) / average_length))
        title_terms = set(terms(f"{chunk.section_title} {Path(chunk.source_file).stem}"))
        score += 1.5 * len(query_terms & title_terms)
        # SQL schemas/fixtures repeat business terms heavily. Prefer descriptive
        # records unless the question asks about storage or data structures.
        if Path(chunk.source_file).suffix.lower() == ".sql" and not query_terms & {
            "sql", "schema", "database", "table", "column", "seed", "data", "stored", "procedure",
        }:
            score *= 0.5
        if score <= 0:
            continue
        score += 0.05 / (1 + vector_ranks[chunk.chunk_id]) if chunk.chunk_id in vector_ranks else 0
        ranked.append((chunk, score))
    return sorted(ranked, key=lambda item: (-item[1], item[0].chunk_id))


def excerpt(text: str, query: str, byte_limit: int) -> str:
    """Choose a contiguous query-relevant passage without rewriting source text."""
    if len(text.encode("utf-8")) <= byte_limit:
        return text
    query_terms = set(terms(query))
    # Consider line starts so sections near the end of a source are not lost.
    starts = [0] + [match.end() for match in re.finditer(r"\n", text)]
    best = ""
    best_score = -1.0
    for start in starts:
        passage = text[start:].encode("utf-8")[:byte_limit].decode("utf-8", errors="ignore")
        if start + len(passage) < len(text) and "\n" in passage:
            boundary = passage.rfind("\n")
            if boundary > len(passage) // 2:
                passage = passage[:boundary]
        words = set(terms(passage))
        score = len(query_terms & words) + min(len(passage), byte_limit) / byte_limit * 0.1
        if score > best_score:
            best, best_score = passage, score
    return best


def select_chunks(ranked: list[tuple[SourceChunk, float]], scope: str, limit: int = 8):
    """Interleave versions and limit repeated files so both fit in the prompt."""
    pools = []
    versions = ("legacy", "mod_v1") if scope == "compare" else (scope,)
    for version in versions:
        counts = Counter()
        pool = []
        for chunk, score in ranked:
            # Structural sections are narrower than the old packed passages.
            # Keep room for a third section without changing the overall budget.
            per_file_limit = 3 if chunk.chunk_strategy in {"python-ast", "prose-structure", "sql-statements"} else 2
            if chunk.system_version != version or counts[chunk.source_file] >= per_file_limit:
                continue
            counts[chunk.source_file] += 1
            pool.append((chunk, score))
        pools.append(pool)
    result = []
    while any(pools) and len(result) < limit:
        for pool in pools:
            if pool and len(result) < limit:
                result.append(pool.pop(0))
    return result
