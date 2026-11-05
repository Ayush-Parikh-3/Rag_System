"""
vector_store.py
Persistent ChromaDB vector store — one collection per repository.
"""

import chromadb
from chromadb.config import Settings


CHROMA_PATH = "./chroma_db"


class VectorStore:
    def __init__(self, collection_name: str):
        self.client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        """Add chunks + pre-computed embeddings to the collection."""
        if not chunks:
            return

        ids        = [str(c["metadata"]["chunk_index"]) for c in chunks]
        documents  = [c["text"] for c in chunks]
        metadatas  = [c["metadata"] for c in chunks]

        # ChromaDB upsert to avoid duplicates on re-index
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(self, query_embedding: list[float], top_k: int = 6) -> list[dict]:
        """
        Returns list of dicts:
            {text, metadata: {path, url, branch, ...}, distance}
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({"text": doc, "metadata": meta, "distance": dist})
        return output

    def count(self) -> int:
        return self.collection.count()
