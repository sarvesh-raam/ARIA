import fitz  # PyMuPDF
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from services.chroma_service import ChromaService
from services.groq_service import GroqService, LLMError


def plain_text(answer: str) -> str:
    """Strip the markdown and 【citation】 markers gpt-oss adds even when asked not to."""
    answer = re.sub(r"【[^】]*】", "", answer)
    answer = re.sub(r"\*\*(.+?)\*\*", r"\1", answer)
    answer = re.sub(r"^#{1,6}\s+", "", answer, flags=re.MULTILINE)
    return re.sub(r"[ \t]+\n", "\n", answer).strip()


class DocumentAgent:
    """
    Phase 1 Agent — Document Intelligence
    Responsibilities:
      - Extract text from uploaded PDFs
      - Chunk the text into searchable pieces
      - Store in ChromaDB vector database
      - Answer natural-language questions using RAG + Groq LLM
    """

    CHUNK_SIZE = 1000   # characters per chunk
    CHUNK_OVERLAP = 200  # overlap to preserve context at boundaries

    def __init__(self):
        self.chroma = ChromaService()
        self.groq = GroqService()

        # Simple JSON file to track uploaded documents
        self.metadata_file = Path("data/documents.json")
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.metadata_file.exists():
            self.metadata_file.write_text("[]")

    # ── Private helpers ──────────────────────────────────────────

    def _load_metadata(self) -> list:
        return json.loads(self.metadata_file.read_text())

    def _save_metadata(self, data: list):
        self.metadata_file.write_text(json.dumps(data, indent=2))

    def _extract_text(self, content: bytes) -> str:
        """Use PyMuPDF to pull raw text from every page of the PDF."""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception:
            raise ValueError("This file could not be read as a PDF. It may be corrupted.")
        if doc.needs_pass:
            doc.close()
            raise ValueError("This PDF is password-protected. Please upload an unlocked copy.")
        pages_text = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                pages_text.append(f"[Page {page_num + 1}]\n{text}")
        doc.close()
        return "\n\n".join(pages_text)

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.
        Overlap ensures that sentences crossing chunk boundaries are captured.
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.CHUNK_SIZE
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.CHUNK_OVERLAP
        return chunks

    def _extract_company_name(self, text: str, filename: str) -> tuple[str, str]:
        """
        Quick heuristic: ask the LLM to extract the company name
        from the first 2000 characters of the document.
        Falls back to the filename if extraction fails.
        Returns (name, source) where source is "llm" or "filename".
        """
        snippet = text[:2000]
        prompt = (
            "From the following document excerpt, extract ONLY the company name "
            "(no explanation, no punctuation, just the name):\n\n" + snippet
        )
        fallback = Path(filename).stem
        try:
            # Headroom for the model's reasoning tokens; the length check below still guards the answer
            name = self.groq.ask(prompt, max_tokens=150).strip()
        except LLMError as e:
            print(f"[DocumentAgent] Company name extraction failed, using filename: {e}")
            return fallback, "filename"
        # If the LLM returns something too long it probably failed
        return (name, "llm") if len(name) < 80 else (fallback, "filename")

    def _repair_existing(self, doc: dict, content: bytes, progress_callback=None) -> list[str]:
        """
        Re-upload of a known document: redo whatever didn't succeed the first time.
          - company name that fell back to the filename -> ask the LLM again
          - vectors missing (e.g. vector DB wiped on restart) -> re-embed
        Updates `doc` in place and returns a list of what was repaired.
        """
        # Records saved before company_source existed: trust the name unless it is just the filename
        source = doc.get("company_source")
        if source is None:
            source = "filename" if doc.get("company") in (None, "Unknown", Path(doc["filename"]).stem) else "llm"
            doc["company_source"] = source

        needs_company = source != "llm"
        needs_vectors = self.chroma.count(doc["doc_id"]) == 0
        if not (needs_company or needs_vectors):
            return []

        if progress_callback: progress_callback(10, "Repairing existing document...")
        text = self._extract_text(content)
        repaired = []
        if needs_company:
            if progress_callback: progress_callback(40, "Identifying company profile...")
            company, source = self._extract_company_name(text, doc["filename"])
            if source == "llm":
                doc["company"], doc["company_source"] = company, source
                repaired.append("company name")
        if needs_vectors:
            if progress_callback: progress_callback(60, "Generating embeddings & storing in vector DB...")
            chunks = self._chunk_text(text)
            self.chroma.add_chunks(doc["doc_id"], chunks)
            doc["chunks"] = len(chunks)
            repaired.append("embeddings")
        return repaired

    # ── Public API ───────────────────────────────────────────────

    def ingest_document(self, content: bytes, filename: str, progress_callback=None) -> dict:
        print(f"DEBUG: ingest_document started for {filename}")
        if progress_callback: progress_callback(5, "Initializing processing...")
        # Stable, reproducible ID based on file content
        doc_id = hashlib.md5(content).hexdigest()[:12]

        # Skip re-processing if already in DB (but fix anything that failed last time)
        metadata = self._load_metadata()
        for doc in metadata:
            if doc["doc_id"] == doc_id:
                repaired = self._repair_existing(doc, content, progress_callback)
                if repaired:
                    self._save_metadata(metadata)
                return {
                    "doc_id": doc_id,
                    "filename": filename,
                    "status": "repaired" if repaired else "already_exists",
                    "message": (
                        f"Document already in the database — repaired {', '.join(repaired)}. Ready to query!"
                        if repaired else "Document already in the database — ready to query!"
                    ),
                    "chunks": doc["chunks"],
                    "company": doc.get("company", "Unknown"),
                }

        # 1. Extract text
        if progress_callback: progress_callback(10, "Extracting text from PDF...")
        text = self._extract_text(content)
        if not text.strip():
            raise ValueError("Could not extract any text from this PDF. Is it scanned/image-only?")

        # 2. Chunk
        if progress_callback: progress_callback(25, "Splitting into semantic chunks...")
        chunks = self._chunk_text(text)

        # 3. Identify company (best-effort)
        if progress_callback: progress_callback(40, "Identifying company profile...")
        company, company_source = self._extract_company_name(text, filename)

        # 4. Store embeddings in ChromaDB
        if progress_callback: progress_callback(60, "Generating embeddings & storing in vector DB...")
        self.chroma.add_chunks(doc_id, chunks)

        if progress_callback: progress_callback(90, "Finalizing metadata...")

        # 5. Persist metadata
        doc_info = {
            "doc_id": doc_id,
            "filename": filename,
            "company": company,
            "company_source": company_source,
            "uploaded_at": datetime.now().isoformat(),
            "chunks": len(chunks),
            "preview": text[:300].strip(),
        }
        metadata.append(doc_info)
        self._save_metadata(metadata)

        return {
            "doc_id": doc_id,
            "filename": filename,
            "company": company,
            "status": "success",
            "message": f"Document processed! {len(chunks)} chunks stored. Ready to query.",
            "chunks": len(chunks),
            "preview": text[:300].strip(),
        }

    def query_document(self, doc_id: str, question: str) -> dict:
        """
        RAG Query:
          1. Embed the question
          2. Find the top-k most relevant chunks in ChromaDB
          3. Send context + question to Groq LLM
          4. Return structured answer
        """
        relevant_chunks = self.chroma.search(doc_id, question, n_results=5)

        if not relevant_chunks:
            return {
                "answer": "No relevant information found for your question in this document.",
                "sources": [],
                "chunks_searched": 0,
            }

        context = "\n\n---\n\n".join(relevant_chunks)

        prompt = f"""You are ARIA, an expert AI financial analyst.
Your job: answer the user's question based ONLY on the document excerpts below.
Be factual, concise, and professional. Cite specific numbers where available.
Answer in plain text: no markdown, no bold, no citation markers.
If the answer is not in the excerpts, say: "This information is not available in the provided document."

DOCUMENT EXCERPTS:
{context}

QUESTION: {question}

ANSWER:"""

        answer = plain_text(self.groq.ask(prompt, max_tokens=1024))

        return {
            "answer": answer,
            "sources": relevant_chunks[:3],   # show top 3 chunks as evidence
            "chunks_searched": len(relevant_chunks),
        }

    def list_documents(self) -> list:
        return self._load_metadata()

    def delete_document(self, doc_id: str) -> dict:
        self.chroma.delete_collection(doc_id)
        metadata = [d for d in self._load_metadata() if d["doc_id"] != doc_id]
        self._save_metadata(metadata)
        return {"status": "deleted", "doc_id": doc_id}
