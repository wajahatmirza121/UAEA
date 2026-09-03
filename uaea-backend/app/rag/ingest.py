"""RAG ingest — chunk + embed + store with version supersession."""

from __future__ import annotations
import os
import uuid
import logging
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeChunk
from app.config import settings

logger = logging.getLogger("rag.ingest")


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text. Uses OpenAI text-embedding-3-small."""
    if settings.embedding_api_key == "sk-REPLACE-ME":
        # Return a zero vector for dev/test without a real API key
        return [0.0] * settings.embedding_dimensions

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.embedding_api_key)
    resp = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
        dimensions=settings.embedding_dimensions,
    )
    return resp.data[0].embedding


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[dict[str, str]]:
    """Split text into overlapping chunks, preserving section headers."""
    sections = text.split("\n\n")
    chunks: list[dict[str, str]] = []
    current_section = ""
    current_text = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Detect section headers (lines starting with § or ##)
        lines = section.split("\n")
        for line in lines:
            if line.startswith("§") or line.startswith("#"):
                if current_text.strip():
                    chunks.append({"section": current_section, "text": current_text.strip()})
                    current_text = ""
                current_section = line.strip()
            else:
                current_text += line + " "

        if len(current_text) > chunk_size:
            # Split oversized sections
            while len(current_text) > chunk_size:
                cut = current_text[:chunk_size]
                # Try to cut at a sentence boundary
                last_period = cut.rfind(". ")
                if last_period > chunk_size // 2:
                    cut = cut[:last_period + 1]
                chunks.append({"section": current_section, "text": cut.strip()})
                current_text = current_text[len(cut) - overlap:]
            current_text = current_text.strip()

    if current_text.strip():
        chunks.append({"section": current_section, "text": current_text.strip()})

    return chunks


async def ingest_document(
    db: AsyncSession,
    source_doc_id: str,
    text: str,
    supersede_old: bool = True,
) -> int:
    """Ingest a document: chunk, embed, store.

    If supersede_old is True, marks old chunks from the same source_doc_id
    as superseded by the new chunks.

    Returns the number of chunks created.
    """
    raw_chunks = chunk_text(text)
    if not raw_chunks:
        logger.warning(f"No chunks produced for {source_doc_id}")
        return 0

    # Embed all chunks
    new_chunk_ids: list[str] = []
    for chunk_data in raw_chunks:
        chunk_id = str(uuid.uuid4())
        new_chunk_ids.append(chunk_id)
        embedding = await get_embedding(chunk_data["text"])

        db.add(KnowledgeChunk(
            id=chunk_id,
            source_doc_id=source_doc_id,
            text=chunk_data["text"],
            embedding=embedding,
            section=chunk_data["section"],
        ))

    # Supersede old chunks from the same document
    if supersede_old:
        old_chunks = await db.execute(
            select(KnowledgeChunk).where(
                KnowledgeChunk.source_doc_id == source_doc_id,
                KnowledgeChunk.id.notin_(new_chunk_ids),
                KnowledgeChunk.superseded_by.is_(None),
            )
        )
        for old in old_chunks.scalars().all():
            old.superseded_by = new_chunk_ids[0] if new_chunk_ids else None

    await db.commit()
    logger.info(f"Ingested {len(raw_chunks)} chunks for {source_doc_id}")
    return len(raw_chunks)


async def ingest_file(
    db: AsyncSession,
    file_path: str,
    source_doc_id: Optional[str] = None,
) -> int:
    """Ingest a file from disk (txt or pdf)."""
    if source_doc_id is None:
        source_doc_id = os.path.splitext(os.path.basename(file_path))[0]

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

    return await ingest_document(db, source_doc_id, text)
