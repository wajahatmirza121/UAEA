"""RAG retrieve — top-k similarity search with basic rerank."""

from __future__ import annotations
import logging
from typing import Any

import numpy as np
from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeChunk
from app.config import settings

logger = logging.getLogger("rag.retrieve")


async def _get_query_embedding(query: str) -> list[float]:
    """Get embedding for a query string."""
    if settings.embedding_api_key == "sk-REPLACE-ME":
        return [0.0] * settings.embedding_dimensions

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.embedding_api_key)
    resp = await client.embeddings.create(
        model=settings.embedding_model,
        input=query,
        dimensions=settings.embedding_dimensions,
    )
    return resp.data[0].embedding


def _embeddings_enabled() -> bool:
    return (settings.embedding_api_key not in ("", "sk-REPLACE-ME")
            and not settings.database_url.startswith("sqlite"))


_STOP = set("""a an the is are was of for to in on at and or what when where which who how much many do does
can i my me you your it this that be with from by as kya kab kahan kis kaun kitni kitna kitne hai hain ho hoga
hogi ka ki ke ko se sy me mein main mujhe mera meri please bata batao""".split())


def _terms(text: str) -> list[str]:
    import re
    from app.orchestrator.normalizer import normalise
    words = re.findall(r"[a-z0-9\u0600-\u06FF]+", normalise(text or ""))
    out = []
    for w in words:
        if w in _STOP or len(w) < 2:
            continue
        # crude stemming so "classes" ~ "class", "results" ~ "result"
        for suf in ("ing", "es", "s"):
            if len(w) > 4 and w.endswith(suf):
                w = w[: -len(suf)]
                break
        out.append(w)
    return out


async def keyword_search(db: AsyncSession, query: str, top_k: int = 5) -> dict[str, Any]:
    """BM25 keyword search over knowledge chunks. Works without embeddings and on SQLite."""
    import math
    rows = (await db.execute(select(KnowledgeChunk).where(KnowledgeChunk.superseded_by.is_(None)))).scalars().all()
    q = _terms(query)
    if not rows or not q:
        return {"chunks": [], "message": "No relevant documents found.", "count": 0}
    docs = [(r, _terms(" ".join([r.section or ""] * 3) + " " + r.text)) for r in rows]
    n = len(docs)
    avgdl = sum(len(d) for _, d in docs) / n
    df: dict[str, int] = {}
    for _, d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    k1, b = 1.4, 0.75
    scored = []
    for r, d in docs:
        score = 0.0
        for t in q:
            tf = d.count(t)
            if not tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(d) / avgdl))
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]
    if not top:
        return {"chunks": [], "message": "No relevant documents found.", "count": 0}
    best = top[0][0]
    chunks = [{
        "id": r.id, "source_doc_id": r.source_doc_id, "text": r.text, "section": r.section,
        "score": round(s / best, 3),
        "last_verified_at": str(r.last_verified_at) if r.last_verified_at else None,
    } for s, r in top if s >= best * 0.35]
    return {
        "chunks": chunks,
        "formatted": "\n\n".join(f"[{c['source_doc_id']} {c['section'] or ''}] {c['text']}" for c in chunks),
        "count": len(chunks),
        "method": "keyword",
    }


async def search_knowledge_base(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Search knowledge chunks.

    Uses pgvector cosine similarity when real embeddings are configured
    (PostgreSQL + EMBEDDING_API_KEY); otherwise BM25 keyword search, which
    works with only a Groq key and on SQLite.
    """
    if not _embeddings_enabled():
        return await keyword_search(db, query, top_k)
    try:
        has_vectors = (await db.execute(sql_text(
            "SELECT 1 FROM knowledge_chunks WHERE embedding IS NOT NULL LIMIT 1"))).first()
    except Exception:
        has_vectors = None
    if not has_vectors:
        return await keyword_search(db, query, top_k)

    query_embedding = await _get_query_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Use pgvector cosine distance operator <=>
    stmt = sql_text("""
        SELECT id, source_doc_id, text, section, last_verified_at,
               1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM knowledge_chunks
        WHERE superseded_by IS NULL AND embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(stmt, {"embedding": embedding_str, "top_k": top_k})
    rows = result.all()

    if not rows:
        return await keyword_search(db, query, top_k)

    # Basic rerank: boost chunks with section headers that match query terms
    query_terms = set(query.lower().split())
    reranked = []
    for row in rows:
        score = float(row.score) if row.score else 0.0
        # Boost if section header contains query terms
        if row.section:
            section_terms = set(row.section.lower().split())
            overlap = len(query_terms & section_terms)
            score += overlap * 0.05

        reranked.append({
            "id": row.id,
            "source_doc_id": row.source_doc_id,
            "text": row.text,
            "section": row.section,
            "score": round(score, 3),
            "last_verified_at": str(row.last_verified_at) if row.last_verified_at else None,
        })

    reranked.sort(key=lambda x: x["score"], reverse=True)

    # Format for the LLM
    formatted = []
    for chunk in reranked[:top_k]:
        source_info = f"[{chunk['source_doc_id']}"
        if chunk["section"]:
            source_info += f" {chunk['section']}"
        source_info += "]"
        formatted.append(f"{source_info} {chunk['text']}")

    return {
        "chunks": reranked,
        "formatted": "\n\n".join(formatted),
        "count": len(reranked),
    }
