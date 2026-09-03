---
kind: external_dependency
name: Database — PostgreSQL 16 with pgvector extension
slug: postgresql-pgvector
category: external_dependency
category_hints:
    - vendor_identity
    - migration_status
scope:
    - '**'
---

### Role
Primary datastore for both relational metadata (departments, services, fees, deadlines, conversations, messages) and vector embeddings for RAG retrieval.

### Integration points
- Docker image `pgvector/pgvector:pg16` launched via `docker-compose.yml`; connection strings supplied as `DATABASE_URL` (asyncpg) and `DATABASE_URL_SYNC` (psycopg2) through `app/config.Settings`.
- Knowledge chunk similarity search uses the pgvector `<=>` cosine distance operator directly in raw SQL inside `retrieve.search_knowledge_base`.
- Alembic migration `alembic/versions/0001_initial.py` creates the `knowledge_chunks` table with a `VECTOR` column.

### Stable usage notes
- Tests run against an in-memory SQLite database (`aiosqlite`) and do NOT use pgvector; production requires the pgvector-enabled Postgres image.
- Re-ingesting a document marks old `KnowledgeChunk` rows via `superseded_by` instead of appending duplicates — this versioning is enforced at the application layer.