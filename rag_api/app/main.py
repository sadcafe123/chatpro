import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .embeddings import EmbeddingModel
from .chunker import chunk_text
from .docling_ingest import extract_text
from .milvus_store import MilvusStore

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG API with Docling + Milvus")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global singletons
_embedding_model = EmbeddingModel()
_collection_name = os.getenv("MILVUS_COLLECTION_NAME", "documents")
_milvus = MilvusStore(
    collection_name=_collection_name,
    vector_dim=_embedding_model.dimension,
)

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class IngestResponse(BaseModel):
    doc_id: str
    num_chunks: int
    collection: str


class QueryRequest(BaseModel):
    query: str = Field(..., description="User's query text")
    top_k: int = Field(5, ge=1, le=50)
    doc_id: Optional[str] = Field(None, description="Filter to a specific document id")


class QueryHit(BaseModel):
    score: float
    doc_id: str
    chunk_index: int
    text: str


class QueryResponse(BaseModel):
    matches: List[QueryHit]


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "collection": _collection_name, "dim": _embedding_model.dimension}


@app.post("/ingest", response_model=List[IngestResponse])
async def ingest(files: List[UploadFile] = File(...)) -> List[IngestResponse]:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    responses: List[IngestResponse] = []
    chunk_size = int(os.getenv("DOC_CHUNK_SIZE", "800"))
    chunk_overlap = int(os.getenv("DOC_CHUNK_OVERLAP", "100"))

    for file in files:
        filename = Path(file.filename or "document").name
        doc_id = os.path.splitext(filename)[0]
        temp_path = UPLOADS_DIR / filename
        with temp_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        text = extract_text(str(temp_path), prefer_docling=True)
        if not text.strip():
            raise HTTPException(status_code=422, detail=f"Failed to extract text from {filename}")

        chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
        embeddings = _embedding_model.embed_documents(chunks)
        payload = list(zip(range(len(chunks)), chunks, embeddings))
        count = _milvus.upsert_chunks(doc_id=doc_id, chunks=payload)
        responses.append(IngestResponse(doc_id=doc_id, num_chunks=count, collection=_collection_name))

    return responses


@app.post("/query", response_model=QueryResponse)
async def query(body: QueryRequest) -> QueryResponse:
    query_vec = _embedding_model.embed_query(body.query)
    hits = _milvus.search(query_vector=query_vec, top_k=body.top_k, doc_id=body.doc_id)
    return QueryResponse(matches=[QueryHit(**h) for h in hits])


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str) -> dict:
    deleted = _milvus.delete_by_doc_id(doc_id)
    return {"doc_id": doc_id, "deleted": deleted}
