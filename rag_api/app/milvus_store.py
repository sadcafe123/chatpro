import os
import time
from typing import Dict, List, Optional, Sequence, Tuple

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)


class MilvusStore:
    def __init__(
        self,
        collection_name: str,
        vector_dim: int,
        metric_type: str = "COSINE",
        host: Optional[str] = None,
        port: Optional[str] = None,
    ) -> None:
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        self.metric_type = metric_type
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = port or os.getenv("MILVUS_PORT", "19530")

        self._connect()
        self.collection = self._get_or_create_collection()
        self._ensure_index()
        self.collection.load()

    def _connect(self) -> None:
        connections.connect(alias="default", host=self.host, port=self.port)

    def _get_or_create_collection(self) -> Collection:
        if utility.has_collection(self.collection_name):
            col = Collection(self.collection_name)
            return col

        pk = FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True)
        doc_id_f = FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128)
        chunk_index_f = FieldSchema(name="chunk_index", dtype=DataType.INT64)
        text_f = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
        embed_f = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim)

        schema = CollectionSchema(
            fields=[pk, doc_id_f, chunk_index_f, text_f, embed_f],
            description="RAG document chunks",
        )
        col = Collection(name=self.collection_name, schema=schema)
        return col

    def _ensure_index(self) -> None:
        # Create HNSW index if not exists
        existing_indexes = {idx.field_name for idx in self.collection.indexes}
        if "embedding" in existing_indexes:
            return
        self.collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": self.metric_type,
                "params": {"M": 8, "efConstruction": 64},
            },
        )

    def upsert_chunks(
        self,
        doc_id: str,
        chunks: Sequence[Tuple[int, str, Sequence[float]]],
    ) -> int:
        # chunks: list of (chunk_index, text, embedding)
        if not chunks:
            return 0
        doc_ids = [doc_id] * len(chunks)
        chunk_indices = [c[0] for c in chunks]
        texts = [c[1] for c in chunks]
        embeddings = [list(c[2]) for c in chunks]
        data = [doc_ids, chunk_indices, texts, embeddings]
        self.collection.insert(data)
        self.collection.flush()
        return len(chunks)

    def delete_by_doc_id(self, doc_id: str) -> int:
        res = self.collection.delete(expr=f'doc_id == "{doc_id}"')
        self.collection.flush()
        return getattr(res, "delete_count", 0) or 0

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
        ef: int = 64,
    ) -> List[Dict]:
        params = {"metric_type": self.metric_type, "params": {"ef": ef}}
        expr = None
        if doc_id:
            expr = f'doc_id == "{doc_id}"'
        results = self.collection.search(
            data=[list(query_vector)],
            anns_field="embedding",
            param=params,
            limit=top_k,
            expr=expr,
            output_fields=["doc_id", "chunk_index", "text"],
        )
        hits = []
        for hit in results[0]:
            hits.append(
                {
                    "score": float(hit.distance),
                    "doc_id": hit.entity.get("doc_id"),
                    "chunk_index": int(hit.entity.get("chunk_index")),
                    "text": hit.entity.get("text"),
                }
            )
        return hits
