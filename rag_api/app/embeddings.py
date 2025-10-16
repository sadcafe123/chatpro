import os
from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self, model_name: str | None = None, normalize: bool = True) -> None:
        resolved_name = model_name or os.getenv(
            "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.model = SentenceTransformer(resolved_name)
        self.normalize = normalize

    @property
    def dimension(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
