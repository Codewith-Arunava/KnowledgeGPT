"""
Vector Store Service — ChromaDB & Pinecone abstraction layer.
Supports: similarity search, MMR search, hybrid search, metadata filtering.
"""
import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Literal
from langchain_core.documents import Document as LCDocument
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embedding import get_embedding_model

logger = get_logger(__name__)


class VectorStoreBase(ABC):
    """Abstract base class for vector store implementations."""

    @abstractmethod
    def add_documents(self, documents: List[LCDocument], collection_name: str) -> None:
        pass

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def mmr_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        fetch_k: int = 20,
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        pass


# ─── ChromaDB Implementation ──────────────────────────────────

class ChromaDBStore(VectorStoreBase):
    def __init__(self, embedding_model: str | None = None):
        self.embedding = get_embedding_model(embedding_model)
        self._stores: Dict[str, Any] = {}

    def _get_store(self, collection_name: str):
        if collection_name not in self._stores:
            from langchain_chroma import Chroma
            import chromadb
            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            self._stores[collection_name] = Chroma(
                client=client,
                collection_name=collection_name,
                embedding_function=self.embedding,
            )
        return self._stores[collection_name]

    def add_documents(self, documents: List[LCDocument], collection_name: str) -> None:
        store = self._get_store(collection_name)
        store.add_documents(documents)
        logger.info("chroma.add_documents", collection=collection_name, count=len(documents))

    def similarity_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        store = self._get_store(collection_name)
        results = store.similarity_search_with_score(query, k=k, filter=filter)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    def mmr_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        fetch_k: int = 20,
    ) -> List[Dict[str, Any]]:
        store = self._get_store(collection_name)
        results = store.max_marginal_relevance_search(query, k=k, fetch_k=fetch_k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": 0.0}
            for doc in results
        ]

    def hybrid_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Combine similarity + MMR for hybrid search."""
        sim = self.similarity_search(query, collection_name, k=k)
        mmr = self.mmr_search(query, collection_name, k=k)
        # Merge, deduplicate by chunk_id
        seen = set()
        merged = []
        for result in sim + mmr:
            cid = result["metadata"].get("chunk_id", "")
            if cid not in seen:
                seen.add(cid)
                merged.append(result)
        return merged[:k]

    def delete_collection(self, collection_name: str) -> None:
        import chromadb
        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        try:
            client.delete_collection(collection_name)
            self._stores.pop(collection_name, None)
            logger.info("chroma.delete_collection", collection=collection_name)
        except Exception as e:
            logger.warning("chroma.delete_collection.failed", collection=collection_name, error=str(e))


# ─── Pinecone Implementation ──────────────────────────────────

class PineconeStore(VectorStoreBase):
    def __init__(self, embedding_model: str | None = None):
        self.embedding = get_embedding_model(embedding_model)
        self._index = None

    def _get_index(self):
        if self._index is None:
            from pinecone import Pinecone
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self._index = pc.Index(settings.PINECONE_INDEX_NAME)
        return self._index

    def add_documents(self, documents: List[LCDocument], collection_name: str) -> None:
        from langchain_pinecone import PineconeVectorStore
        store = PineconeVectorStore.from_documents(
            documents,
            self.embedding,
            index_name=settings.PINECONE_INDEX_NAME,
            namespace=collection_name,
        )
        logger.info("pinecone.add_documents", namespace=collection_name, count=len(documents))

    def similarity_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        from langchain_pinecone import PineconeVectorStore
        store = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embedding,
            namespace=collection_name,
        )
        results = store.similarity_search_with_score(query, k=k, filter=filter)
        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": float(score)}
            for doc, score in results
        ]

    def mmr_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        fetch_k: int = 20,
    ) -> List[Dict[str, Any]]:
        from langchain_pinecone import PineconeVectorStore
        store = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embedding,
            namespace=collection_name,
        )
        results = store.max_marginal_relevance_search(query, k=k, fetch_k=fetch_k)
        return [{"content": doc.page_content, "metadata": doc.metadata, "score": 0.0} for doc in results]

    def hybrid_search(self, query: str, collection_name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self.similarity_search(query, collection_name, k=k)

    def delete_collection(self, collection_name: str) -> None:
        index = self._get_index()
        index.delete(delete_all=True, namespace=collection_name)
        logger.info("pinecone.delete_namespace", namespace=collection_name)


# ─── Factory ─────────────────────────────────────────────────

def get_vector_store(
    store_type: str | None = None,
    embedding_model: str | None = None,
) -> VectorStoreBase:
    store_type = store_type or settings.DEFAULT_VECTOR_STORE
    if store_type == "pinecone" and settings.has_pinecone:
        return PineconeStore(embedding_model)
    return ChromaDBStore(embedding_model)
