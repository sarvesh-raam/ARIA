try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("\n[!] WARNING: ChromaDB not found. Starting ARIA in 'Lite Mode'.")
    print("[!] Internal PDF search will be simulated, but Live Market Fusion (Phase 2) will work!\n")

from pathlib import Path

class ChromaService:
    """
    Wrapper around ChromaDB — our private, local vector database.
    Each document gets its own isolated collection (named by doc_id).

    Lite Mode: If ChromaDB is missing (e.g. C++ build tools), ARIA uses 
    a simulation mode to allow external NewsAI and Reporting to function.
    """

    def __init__(self):
        self.mock_db = {} # Simple in-memory store for Lite Mode
        global CHROMA_AVAILABLE
        if CHROMA_AVAILABLE:
            try:
                db_path = Path("data/chroma_db")
                db_path.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=str(db_path))
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            except Exception as e:
                print(f"[ChromaService] Error initializing real DB: {e}. Falling back to Lite.")
                CHROMA_AVAILABLE = False

    def _get_collection(self, doc_id: str):
        if CHROMA_AVAILABLE:
            return self.client.get_or_create_collection(
                name=f"doc_{doc_id.replace('-', '_')}",
                embedding_function=self.embedding_fn,
            )
        return None

    def add_chunks(self, doc_id: str, chunks: list[str]):
        if CHROMA_AVAILABLE:
            collection = self._get_collection(doc_id)
            collection.add(
                documents=chunks,
                ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
                metadatas=[{"chunk_index": i} for i in range(len(chunks))],
            )
        else:
            # Lite Mode: Store in memory simply
            self.mock_db[doc_id] = chunks

    def search(self, doc_id: str, query: str, n_results: int = 5) -> list[str]:
        if CHROMA_AVAILABLE:
            try:
                collection = self._get_collection(doc_id)
                count = collection.count()
                if count == 0: return []
                results = collection.query(query_texts=[query], n_results=min(n_results, count))
                return results["documents"][0] if results["documents"] else []
            except Exception as e:
                print(f"[ChromaService] Search error: {e}")
                return []
        else:
            # Lite Mode: Return the first few lines of the document as a "simulation"
            return self.mock_db.get(doc_id, ["(Simulation) Document intelligence is active. No local vector DB found."])[:n_results]

    def delete_collection(self, doc_id: str):
        if CHROMA_AVAILABLE:
            try:
                self.client.delete_collection(f"doc_{doc_id.replace('-', '_')}")
            except Exception: pass
        else:
            self.mock_db.pop(doc_id, None)

    def list_collections(self):
        if CHROMA_AVAILABLE:
            return [c.name for c in self.client.list_collections()]
        return list(self.mock_db.keys())
