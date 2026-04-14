from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from pathlib import Path
from typing import Dict
from fastapi.concurrency import run_in_threadpool
from sse_starlette.sse import EventSourceResponse
import sys

# Make sure local modules are importable
sys.path.append(str(Path(__file__).parent))

from agents.document_agent import DocumentAgent
from agents.risk_agent import RiskAgent
from models.schemas import QueryRequest, RiskReport

app = FastAPI(
    title="ARIA - Autonomous Risk Intelligence Agent",
    description="AI-powered financial document risk analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "https://aria-six-phi.vercel.app",
        "https://aria-audit.vercel.app" # Future-proofing for your custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
doc_agent = DocumentAgent()
risk_agent = RiskAgent(doc_agent)

# Progress tracking
# Structure: { progress_id: {"percentage": int, "status": str} }
progress_store: Dict[str, Dict] = {}

def update_progress(progress_id: str, percentage: int, status: str):
    progress_store[progress_id] = {"percentage": percentage, "status": status}
    print(f"[Progress {progress_id}] {percentage}% - {status}")

@app.get("/api/progress/{progress_id}")
async def progress_stream(progress_id: str):
    """SSE endpoint to stream progress for a specific task."""
    async def event_generator():
        last_percent = -1
        while True:
            if progress_id in progress_store:
                data = progress_store[progress_id]
                # Only send if progress changed
                if data["percentage"] != last_percent:
                    yield {
                        "data": json.dumps(data)
                    }
                    last_percent = data["percentage"]
                
                if data["percentage"] >= 100:
                    break
            await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())

# ─────────────────────────────────────────────
#  HEALTH CHECK
# ─────────────────────────────────────────────
@app.get("/")
def health_check():
    return {
        "status": "ARIA Intelligence System Online",
        "phase": "Phase 1 - Document Intelligence",
        "version": "1.0.0"
    }

# ─────────────────────────────────────────────
#  UPLOAD A DOCUMENT
# ─────────────────────────────────────────────
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), task_id: str = None):
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

    # Use task_id if provided, else use hash
    import hashlib
    content_hash = hashlib.md5(content).hexdigest()[:12]
    progress_id = task_id if task_id else content_hash
    
    def sync_ingest():
        print(f"Starting ingest for {file.filename} (Progress ID: {progress_id})")
        return doc_agent.ingest_document(
            content, 
            file.filename, 
            progress_callback=lambda p, s: update_progress(progress_id, p, s)
        )

    result = await run_in_threadpool(sync_ingest)
    
    # Map the progress to the actual doc_id as well for future analysis steps
    doc_id = result["doc_id"]
    if progress_id != doc_id:
        update_progress(doc_id, progress_store.get(progress_id, {}).get("percentage", 100), "Handoff complete")

    update_progress(progress_id, 100, "Upload complete!")
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

    result = doc_agent.query_document(request.doc_id, request.question)
    return result

# ─────────────────────────────────────────────
#  LIST ALL DOCUMENTS
# ─────────────────────────────────────────────
@app.get("/api/documents")
async def list_documents():
    """Return all documents that have been uploaded and processed."""
    return doc_agent.list_documents()

# ─────────────────────────────────────────────
#  DELETE A DOCUMENT
# ─────────────────────────────────────────────
@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Remove a document and all its stored data."""
    return doc_agent.delete_document(doc_id)


# ─────────────────────────────────────────────
#  FULL RISK ANALYSIS (Phase 2)
# ─────────────────────────────────────────────
@app.get("/api/analyze/{doc_id}", response_model=RiskReport)
async def analyze_document(doc_id: str):
    """
    Perform a multi-source risk analysis:
    1. Financial anomaly detection (Internal)
    2. Live news sentiment analysis (External)
    3. Aggregated risk scoring
    """
    def sync_analyze():
        print(f"Starting analysis for doc {doc_id}")
        return risk_agent.run_full_analysis(
            doc_id, 
            progress_callback=lambda p, s: update_progress(doc_id, p, s)
        )

    result = await run_in_threadpool(sync_analyze)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    update_progress(doc_id, 100, "Analysis complete!")
    return result


# ─────────────────────────────────────────────
#  GENERATE PDF REPORT (Phase 3)
# ─────────────────────────────────────────────
@app.get("/api/report/{doc_id}")
async def get_pdf_report(doc_id: str):
    """
    Generate and download a professional PDF risk report for a document.
    """
    try:
        pdf_path = risk_agent.generate_report(doc_id)
        return FileResponse(
            path=pdf_path, 
            filename=Path(pdf_path).name,
            media_type='application/pdf'
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
