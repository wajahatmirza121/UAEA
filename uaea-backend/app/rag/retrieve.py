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


async def search_knowledge_base(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Search for relevant chunks using pgvector cosine similarity.

    Returns a dict with 'chunks' list containing scored results.
    Suitable as a tool call result for the LLM.
    """
    query_embedding = await _get_query_embedding(query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # Use pgvector cosine distance operator <=>
    stmt = sql_text("""
        SELECT id, source_doc_id, text, section, last_verified_at,
               1 - (embedding <=> :embedding::vector) AS score
        FROM knowledge_chunks
        WHERE superseded_by IS NULL
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(stmt, {"embedding": embedding_str, "top_k": top_k})
    rows = result.all()

    if not rows:
        return {"chunks": [], "message": "No relevant documents found."}

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
