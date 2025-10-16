# Open WebUI + Milvus + Docling RAG Stack

This repository provides a minimal, production-ready stack to run:
- Open WebUI (LLM chat UI)
- Milvus (vector database)
- A Python FastAPI service (rag-api) that uses Docling to parse documents, chunks them, embeds with SentenceTransformers, and stores/searches vectors in Milvus.

## Quick start

1. Bring everything up:

```bash
docker compose up -d --build
```

2. Access services:
- Open WebUI: `http://localhost:8080`
- RAG API docs (FastAPI): `http://localhost:8000/docs`
- Milvus (gRPC): `localhost:19530`

3. Ingest a document into Milvus via RAG API:

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/your.pdf"
```

4. Query:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?", "top_k": 5}'
```

5. Use in Open WebUI:
- Configure your preferred LLM provider in the Open WebUI settings (e.g., OpenAI API key or Ollama).
- Optionally, create a custom Tool in Open WebUI that calls the RAG API `/query` endpoint and displays the returned context in responses.

## Notes
- The RAG API uses Docling by default for parsing documents, falling back to a simple parser for unsupported files.
- The embedding model defaults to `sentence-transformers/all-MiniLM-L6-v2`. You can change it via the `EMBEDDING_MODEL_NAME` environment variable in `docker-compose.yml`.
- Collection name can be configured with `MILVUS_COLLECTION_NAME`.
- Uploaded files are stored in the `./data/uploads` directory (mounted into the container as `/data/uploads`).

## Maintenance
- Stop services: `docker compose down`
- Remove volumes (data loss): `docker compose down -v`

## Troubleshooting
- If Docling installation fails on your platform, you may need additional system packages or to pin a specific `docling` version compatible with your environment.
- If embedding downloads are slow on first run, it's the model being downloaded. Subsequent runs will be faster.
