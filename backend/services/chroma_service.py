import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path


class ChromaService:
    """
    Wrapper around ChromaDB — our private, local vector database.
    Each document gets its own isolated collection (named by doc_id).

    Embedding model: all-MiniLM-L6-v2 (runs locally, free, fast, 384-dim)
    """

    def __init__(self):
        db_path = Path("data/chroma_db")
        db_path.mkdir(parents=True, exist_ok=True)

        # PersistentClient saves the DB to disk so data survives restarts
        self.client = chromadb.PersistentClient(path=str(db_path))

        # Local sentence-transformer model — no API key needed
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def _get_collection(self, doc_id: str):
        """Get or create a ChromaDB collection for a specific document."""
        return self.client.get_or_create_collection(
            name=f"doc_{doc_id}",
            embedding_function=self.embedding_fn,
        )

    def add_chunks(self, doc_id: str, chunks: list[str]):
        """
        Embed and store all chunks for a document.
        Each chunk gets a unique ID so we can retrieve it later.
        """
        collection = self._get_collection(doc_id)

        # ChromaDB expects: documents, ids (and optionally metadatas)
        collection.add(
            documents=chunks,
            ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
            metadatas=[{"chunk_index": i} for i in range(len(chunks))],
        )

    def search(self, doc_id: str, query: str, n_results: int = 5) -> list[str]:
        """
        Semantic search: find the top-n chunks most relevant to the query.
        Returns a list of raw text strings.
        """
        try:
            collection = self._get_collection(doc_id)
            count = collection.count()
            if count == 0:
                return []

            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, count),
            )
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            print(f"[ChromaService] Search error: {e}")
            return []

    def delete_collection(self, doc_id: str):
        """Remove all data for a document."""
        try:
            self.client.delete_collection(f"doc_{doc_id}")
        except Exception:
            pass  # Already deleted or never existed
