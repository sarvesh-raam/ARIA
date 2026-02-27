from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import sys

# Make sure local modules are importable
sys.path.append(str(Path(__file__).parent))

from agents.document_agent import DocumentAgent
from models.schemas import QueryRequest

app = FastAPI(
    title="ARIA - Autonomous Risk Intelligence Agent",
    description="AI-powered financial document risk analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the document agent (loads ChromaDB + Groq)
agent = DocumentAgent()

# ─────────────────────────────────────────────
#  HEALTH CHECK
# ─────────────────────────────────────────────
@app.get("/")
def health_check():
    return {
        "status": "ARIA is online ✅",
        "phase": "Phase 1 — Document Intelligence",
        "version": "1.0.0"
    }

# ─────────────────────────────────────────────
#  UPLOAD A DOCUMENT
# ─────────────────────────────────────────────
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document.
    ARIA will read it, chunk it, and store it in the vector database.
    Returns a doc_id you use for all future queries on this document.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    result = agent.ingest_document(content, file.filename)
    return result

# ─────────────────────────────────────────────
#  ASK A QUESTION ABOUT A DOCUMENT
# ─────────────────────────────────────────────
@app.post("/api/query")
async def query_document(request: QueryRequest):
    """
    Ask any natural-language question about a previously uploaded document.
    ARIA finds the most relevant sections and answers using the LLM.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = agent.query_document(request.doc_id, request.question)
    return result

# ─────────────────────────────────────────────
#  LIST ALL DOCUMENTS
# ─────────────────────────────────────────────
@app.get("/api/documents")
async def list_documents():
    """Return all documents that have been uploaded and processed."""
    return agent.list_documents()

# ─────────────────────────────────────────────
#  DELETE A DOCUMENT
# ─────────────────────────────────────────────
@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document and all its stored data."""
    return agent.delete_document(doc_id)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
