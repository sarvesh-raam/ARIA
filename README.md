# ARIA — Autonomous Risk Intelligence Agent

<div align="center">

![ARIA Banner](https://img.shields.io/badge/ARIA-Autonomous%20Risk%20Intelligence%20Agent-blueviolet?style=for-the-badge&logo=robot)

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama--3%2070B-orange?style=flat-square)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-red?style=flat-square)](https://trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**An AI agent that reads financial documents, searches live news, detects hidden risk signals, and auto-generates risk reports — in 30 seconds.**

[🚀 Live Demo](#) · [📖 Docs](#api-endpoints) · [🛠️ Setup](#setup)

</div>

---

## 🎯 What is ARIA?

ARIA is a **multi-agent AI system** that automates financial risk analysis. It does what a junior analyst spends 3 hours doing — every morning, every day — in under 30 seconds.

> *"ChatGPT answers your questions. ARIA automatically reads 200 pages, connects dots across sources, and delivers a risk report — without you doing anything."*

### The Problem It Solves
Banks and investment firms have analysts who manually:
- Read 200-page company annual reports
- Search for related financial news
- Cross-reference data for inconsistencies
- Write risk summaries for decision-makers

**ARIA automates this entire workflow.**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ARIA — Agent Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PDF Upload ──► Document Agent ──► ChromaDB (embeddings)    │
│                      │                                      │
│                       ──► News Agent ──► NewsAPI            │
│                      │                                      │
│                       ──► Risk Agent ──► Anomaly Detection  │
│                      │                                      │
│                       ──► Groq LLM ──► Llama-3 70B         │
│                      │                                      │
│                       ──► Report Agent ──► PDF Export       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | Groq — Llama-3 70B | AI reasoning engine (free) |
| **Embeddings** | sentence-transformers | Local semantic search (free) |
| **Vector DB** | ChromaDB | Private document storage |
| **PDF Parsing** | PyMuPDF | Fast text extraction |
| **Backend** | FastAPI | REST API server |
| **Frontend** | Next.js (Phase 4) | Dashboard UI |

> 💡 **All free.** No paid APIs required to run this project.

---

## 🗺️ Project Phases

| Phase | Status | What It Builds |
|---|---|---|
| **Phase 1** | ✅ Complete | Document Intelligence — Upload PDF, ask questions via RAG |
| **Phase 2** | 🔄 In Progress | News Agent — Live news search + financial anomaly detection |
| **Phase 3** | 📅 Planned | Agent Pipeline + PDF report generation |
| **Phase 4** | 📅 Planned | Dashboard UI + Deployment |

---

## 🚀 Setup

### Prerequisites
- Python 3.11+
- Free [Groq API key](https://console.groq.com) (takes 30 seconds)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/sarvesh-raam/ARIA.git
cd ARIA/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 4. Start the server
python main.py
```

### Server is running!
- API: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### `POST /api/upload`
Upload a PDF document for analysis.

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@annual_report.pdf"
```

**Response:**
```json
{
  "doc_id": "a1b2c3d4e5f6",
  "company": "Infosys Limited",
  "status": "success",
  "chunks": 347,
  "message": "Document processed! 347 chunks stored."
}
```

---

### `POST /api/query`
Ask any natural-language question about the document.

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "a1b2c3d4e5f6", "question": "What is the revenue growth?"}'
```

**Response:**
```json
{
  "answer": "Infosys reported revenue of ₹1,53,670 crore in FY2024, a 4.2% growth over FY2023's ₹1,47,483 crore...",
  "sources": ["[Page 42] Revenue from operations grew...", "..."],
  "chunks_searched": 5
}
```

---

### `GET /api/documents`
List all uploaded documents.

### `DELETE /api/documents/{doc_id}`
Remove a document from the database.

---

## 🧠 How It Works (Technical Deep Dive)

### 1. Document Ingestion (RAG Pipeline)
```
PDF bytes
  → PyMuPDF extracts text page by page
  → RecursiveTextSplitter chunks into 1000-char pieces with 200-char overlap
  → sentence-transformers embeds each chunk (all-MiniLM-L6-v2, 384-dim)
  → ChromaDB stores embeddings in a per-document collection
```

### 2. Querying (Semantic Search + LLM)
```
User question
  → Embedded using same model
  → ChromaDB finds top-5 most semantically similar chunks
  → Chunks + question sent to Groq (Llama-3 70B)
  → LLM generates a factual, cited answer
```

### Why RAG instead of just ChatGPT?
- **Privacy**: Documents never leave your server
- **Scale**: Handles 500+ page documents (ChatGPT context limit: ~50 pages)
- **Accuracy**: Answers are grounded in the actual document, not hallucinated
- **Speed**: Groq inference: ~500 tokens/second (10× faster than OpenAI)

---

## 🎓 Skills Demonstrated

```
✅ RAG (Retrieval Augmented Generation)    — Modern AI engineering pattern
✅ Vector Databases (ChromaDB)             — Industry-standard for AI apps
✅ LLM Integration (Groq/Llama-3)         — Production AI systems
✅ Multi-Agent Architecture (LangGraph)    — Phase 3
✅ REST API Design (FastAPI)               — Backend engineering
✅ PDF Document Processing (PyMuPDF)       — Data engineering
✅ Semantic Search                         — NLP/ML
✅ Explainable AI                          — Responsible AI
```

---

## 📊 Use Cases

| Industry | Use Case |
|---|---|
| **Banking** (JP Morgan, Barclays) | Automated credit risk analysis from borrower documents |
| **Investment** (Fidelity, BNY) | Portfolio risk screening from company filings |
| **Consulting** (PWC, Accenture) | Audit document intelligence |
| **FinTech** (Visa, Leap Finance) | Fraud pattern detection in transaction records |
| **Enterprise** (Oracle, IBM) | Internal document Q&A and compliance checking |

---

## 🛣️ Roadmap

- [x] Phase 1: Document Intelligence (RAG + Q&A)
- [ ] Phase 2: News Agent (live news + anomaly detection)
- [ ] Phase 3: Full agent pipeline + PDF report export
- [ ] Phase 4: Dashboard UI (Next.js) + cloud deployment
- [ ] Phase 5: Multi-document cross-analysis

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<div align="center">

Built by [Sarvesh Raam T K](https://github.com/sarvesh-raam) · AI Engineering Student @ SRM University

*"The future of financial analysis is autonomous."*

</div>
