# ARIA: Autonomous Risk Intelligence Agent
> **An enterprise-grade AI auditing ecosystem designed to identify clinical and financial risks through cross-referencing internal documentation with real-time global market data.**

[![CI Build](https://github.com/sarvesh-raam/ARIA/actions/workflows/ci.yml/badge.svg)](https://github.com/sarvesh-raam/ARIA/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9+-yellow.svg)](#)
[![Next.js Version](https://img.shields.io/badge/next.js-14.x-black.svg)](#)

---

## 1. Executive Summary
ARIA (Autonomous Risk Intelligence Agent) is a professional AI-driven risk management system. It provides automated detection of clinical and financial anomalies within corporate documents by integrating Retrieval-Augmented Generation (RAG) with live external data fusion. Designed for high-stakes environments, ARIA transforms static reports into dynamic risk intelligence.

## 2. Problem & Solution
**The Challenge:** Manual auditing of extensive corporate and clinical documents is prone to human error, time-consuming, and often lacks context from real-time events. Analysts struggle to cross-reference internal claims against external market shifts, lawsuits, or reputational risks.

**The Solution:** ARIA automates the entire audit lifecycle. By extracting data from complex PDFs and utilizing the Llama 3.3 70B model, it identifies internal discrepancies. Simultaneously, it pulls live global news and performs sentiment analysis, providing a unified, data-driven Risk Score that incorporates both internal validity and external volatility.

## 3. Core Features
- **Intelligent RAG Pipeline**: High-precision PDF text extraction and semantic search powered by ChromaDB for full-context document analysis.
- **Large Language Model Orchestration**: Integration with Llama 3.3 70B via Groq for high-performance, low-latency reasoning and decision support.
- **External Market Fusion**: Real-time integration with global datasets to detect external risks such as legal disputes and management changes.
- **Automated Risk Scoring**: A proprietary algorithm that calculates a 0-100 Risk Score based on internal document anomalies and external market sentiment.
- **Advanced Executive Reporting**: Generation of automated, presentation-ready PDF reports with detailed risk indicators and sectioned insights.
- **Enterprise-Grade Dashboard**: A professional Next.js 14 interface featuring real-time Server-Sent Events (SSE) for transparent analysis progress tracking.

## 4. Tech Stack
-   **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion
-   **Backend**: FastAPI, Uvicorn, Python 3.9+
-   **AI Engines**: Groq (Llama 3.3 70B), Sentence-Transformers (Local Embeddings)
-   **Data Storage**: ChromaDB (Vector Database)
-   **Analysis Utilities**: NewsAPI, PyPDF2, FPDF2

## 5. Architecture
```text
├── .github/          # CI/CD Workflows & Issue Templates
├── backend/          # Python FastAPI Service
│   ├── agents/       # AI Logic & RAG Orchestration
│   ├── services/     # External API Integration (News, PDF Gen)
│   ├── models/       # Data Schemas & ML Models
│   └── main.py       # API Entry Point
├── frontend/         # Next.js Application
│   ├── src/          # Source Code
│   │   ├── components/ # UI Components (NextUI/Tailwind)
│   │   └── hooks/      # State & API Communication Tasks
│   └── tailwind.config.js # Styling Configuration
├── LICENSE           # MIT License
└── README.md         # Documentation
```

## 6. Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher (LTS)
- Groq API Key
- NewsAPI Key

### Step 1: Backend Configuration
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Configure Environment Variables in backend/.env
python main.py
```

### Step 2: Frontend Configuration
```bash
cd frontend
npm install
npm run dev
```

## 7. Roadmap
-   **Multi-Agent Orchestration**: Implement LangGraph to facilitate collaborative agent reasoning for increased risk detection accuracy.
-   **Direct SEC Integration**: Implement automated pulling of company filings through Ticker-based lookups.
-   **Critical Alert System**: Integrate SendGrid for automated stakeholder notification on high-risk detections.
-   **Semantic Graph Visualization**: Deploy Neo4j to visualize complex corporate hierarchies and subsidiary relationships.

## 8. License
Distributed under the MIT License. See `LICENSE` for more information.

---

**Corporate Notice**: This system is designed for professional use by financial and clinical analysts. For enterprise distribution or custom integrations, please contact the maintainers.
