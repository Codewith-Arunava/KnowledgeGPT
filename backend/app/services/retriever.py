"""
Retriever Service — LangChain & LlamaIndex retriever implementations.
Toggle between them per knowledge base.
"""
from typing import List, Dict, Any, Literal, Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.services.embedding import get_embedding_model
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)


class LangChainRetriever:
    """Standard LangChain retriever with multiple search strategies."""

    def __init__(
        self,
        collection_name: str,
        embedding_model: str | None = None,
        vector_store_type: str | None = None,
    ):
        self.collection_name = collection_name
        self.store = get_vector_store(vector_store_type, embedding_model)

    def retrieve(
        self,
        query: str,
        search_type: Literal["similarity", "mmr", "hybrid"] = "similarity",
        k: int = settings.TOP_K_RESULTS,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        logger.info(
            "langchain.retrieve",
            collection=self.collection_name,
            search_type=search_type,
            k=k,
        )
        if search_type == "mmr":
            return self.store.mmr_search(self.collection_name, query, k=k)
        elif search_type == "hybrid":
            return self.store.hybrid_search(query, self.collection_name, k=k)
        else:
            return self.store.similarity_search(query, self.collection_name, k=k, filter=filter)


class LlamaIndexRetriever:
    """LlamaIndex VectorStoreIndex retriever."""

    def __init__(
        self,
        collection_name: str,
        embedding_model: str | None = None,
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model or settings.DEFAULT_EMBEDDING_MODEL

    def _build_index(self):
        """Build a LlamaIndex VectorStoreIndex backed by ChromaDB."""
        import chromadb
        from llama_index.core import VectorStoreIndex, StorageContext
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.core import Settings as LISettings

        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        chroma_collection = client.get_or_create_collection(self.collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Set embedding model
        if self.embedding_model in ("openai-small", "openai-large"):
            model_name = (
                "text-embedding-3-small"
                if self.embedding_model == "openai-small"
                else "text-embedding-3-large"
            )
            LISettings.embed_model = OpenAIEmbedding(
                model=model_name, api_key=settings.OPENAI_API_KEY
            )

        index = VectorStoreIndex.from_vector_store(
            vector_store, storage_context=storage_context
        )
        return index

    def retrieve(
        self,
        query: str,
        search_type: str = "similarity",
        k: int = settings.TOP_K_RESULTS,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        logger.info("llamaindex.retrieve", collection=self.collection_name, k=k)
        try:
            index = self._build_index()
            retriever = index.as_retriever(similarity_top_k=k)
            nodes = retriever.retrieve(query)
            return [
                {
                    "content": node.get_content(),
                    "metadata": node.metadata,
                    "score": float(node.score) if node.score else 0.0,
                }
                for node in nodes
            ]
        except Exception as e:
            logger.error("llamaindex.retrieve.failed", error=str(e))
            # Fallback to LangChain
            lc = LangChainRetriever(self.collection_name)
            return lc.retrieve(query, k=k)


def get_retriever(
    collection_name: str,
    retriever_type: str | None = None,
    embedding_model: str | None = None,
    vector_store_type: str | None = None,
):
    """Factory: return LangChain or LlamaIndex retriever."""
    retriever_type = retriever_type or settings.DEFAULT_RETRIEVER
    if retriever_type == "llamaindex":
        return LlamaIndexRetriever(collection_name, embedding_model)
    return LangChainRetriever(collection_name, embedding_model, vector_store_type)
