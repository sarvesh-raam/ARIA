from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from pathlib import Path
from typing import Dict
from fastapi.concurrency import run_in_threadpool
from sse_starlette.sse import EventSourceResponse
import sys
import os

# Make sure local modules are importable
sys.path.append(str(Path(__file__).parent))

from agents.document_agent import DocumentAgent
from agents.risk_agent import RiskAgent
from services.groq_service import LLMError
from services.security import ai_rate_limit, is_admin, require_admin
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
        "https://aria-intelligence.vercel.app",
        "https://aria-six-phi.vercel.app" # Keeping old one as backup for now
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(LLMError)
async def llm_error_handler(request, exc: LLMError):
    """The AI backend failed — report it instead of returning a made-up result."""
    print(f"[LLMError] {request.url.path}: {exc}")
    return JSONResponse(status_code=502, content={"detail": f"AI analysis failed: {exc}"})

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
PROGRESS_STREAM_MAX_SECONDS = 15 * 60  # longer than any real upload + analysis

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
        # Stop eventually even if the task never reports (unknown ID, crashed worker)
        deadline = asyncio.get_running_loop().time() + PROGRESS_STREAM_MAX_SECONDS
        while asyncio.get_running_loop().time() < deadline:
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
@app.post("/api/upload", dependencies=[Depends(ai_rate_limit)])
async def upload_document(file: UploadFile = File(...), task_id: str = None):
    """
    Upload a PDF document.
    ARIA will read it, chunk it, and store it in the vector database.
    Returns a doc_id you use for all future queries on this document.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read in 1 MB pieces so an oversized upload is rejected without loading it all
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    content = b""
    while piece := await file.read(1024 * 1024):
        content += piece
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File is too large (max {MAX_UPLOAD_MB} MB)")
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

    try:
        result = await run_in_threadpool(sync_ingest)
    except Exception as e:
        update_progress(progress_id, 100, "Upload failed")
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise
    
    # Map the progress to the actual doc_id as well for future analysis steps
    doc_id = result["doc_id"]
    if progress_id != doc_id:
        update_progress(doc_id, progress_store.get(progress_id, {}).get("percentage", 100), "Handoff complete")

    if result["status"] == "repaired":
        # Company name or content changed, so the saved analysis is out of date
        risk_agent.clear_analysis(doc_id)

    update_progress(progress_id, 100, "Upload complete!")
    return result

# ─────────────────────────────────────────────
#  ASK A QUESTION ABOUT A DOCUMENT
# ─────────────────────────────────────────────
@app.post("/api/query", dependencies=[Depends(ai_rate_limit)])
async def query_document(request: QueryRequest):
    """
    Ask any natural-language question about a previously uploaded document.
    ARIA finds the most relevant sections and answers using the LLM.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    return await run_in_threadpool(doc_agent.query_document, request.doc_id, request.question)

# ─────────────────────────────────────────────
#  LIST ALL DOCUMENTS
# ─────────────────────────────────────────────
PUBLIC_DOCUMENT_FIELDS = ("doc_id", "company", "uploaded_at", "chunks")

@app.get("/api/documents")
async def list_documents(admin: bool = Depends(is_admin)):
    """
    Return all documents that have been uploaded and processed.
    Without the admin key only non-sensitive fields are returned (no filenames or text previews).
    """
    docs = doc_agent.list_documents()
    if admin:
        return docs
    return [{k: d.get(k) for k in PUBLIC_DOCUMENT_FIELDS} for d in docs]

# ─────────────────────────────────────────────
#  DELETE A DOCUMENT
# ─────────────────────────────────────────────
@app.delete("/api/documents/{doc_id}", dependencies=[Depends(require_admin)])
async def delete_document(doc_id: str):
    """Remove a document and all its stored data."""
    risk_agent.clear_analysis(doc_id)
    return doc_agent.delete_document(doc_id)


# ─────────────────────────────────────────────
#  SAVED ANALYSIS (no LLM call — used to reopen past audits)
# ─────────────────────────────────────────────
@app.get("/api/analysis/{doc_id}", response_model=RiskReport)
async def get_saved_analysis(doc_id: str):
    """Return the last analysis for a document, or 404 if it has never been analyzed."""
    analysis = risk_agent.load_analysis(doc_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="No saved analysis for this document. Run a new analysis.")
    return analysis


# ─────────────────────────────────────────────
#  FULL RISK ANALYSIS (Phase 2)
# ─────────────────────────────────────────────
@app.get("/api/analyze/{doc_id}", response_model=RiskReport, dependencies=[Depends(ai_rate_limit)])
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

    try:
        result = await run_in_threadpool(sync_analyze)
    except Exception as e:
        update_progress(doc_id, 100, "Analysis failed")
        if isinstance(e, ValueError):
            raise HTTPException(status_code=422, detail=str(e))
        raise
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    update_progress(doc_id, 100, "Analysis complete!")
    return result


# ─────────────────────────────────────────────
#  GENERATE PDF REPORT (Phase 3)
# ─────────────────────────────────────────────
@app.get("/api/report/{doc_id}", dependencies=[Depends(ai_rate_limit)])
async def get_pdf_report(doc_id: str):
    """
    Generate and download a professional PDF risk report for a document.
    """
    try:
        pdf_path = await run_in_threadpool(risk_agent.generate_report, doc_id)
        return FileResponse(
            path=pdf_path, 
            filename=Path(pdf_path).name,
            media_type='application/pdf'
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
