---
kind: external_dependency
name: Embedding Provider — OpenAI text-embedding-3-small
slug: openai-embeddings
category: external_dependency
category_hints:
    - vendor_identity
    - client_constraint
scope:
    - '**'
---

### Role
Generates vector embeddings for knowledge chunks and queries consumed by pgvector cosine similarity search in the RAG pipeline.

### Integration points
- `AsyncOpenAI` client created inside `retrieve._get_query_embedding` using `settings.embedding_api_key`.
- Model name and dimensionality controlled by `embedding_model` (`text-embedding-3-small`) and `embedding_dimensions` (384) in `config.Settings`.
- When `embedding_api_key` is left at the placeholder value, the function falls back to a zero-vector so retrieval still works without an OpenAI key.

### Stable usage notes
- The embedding provider is currently hardcoded to OpenAI; swapping to BGE-M3 would require adding a provider switch in `config` and branching `_get_query_embedding`. The pgvector schema expects vectors of `embedding_dimensions` length, so any replacement model must match that size.