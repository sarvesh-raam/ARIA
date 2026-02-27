# 🛡️ ARIA: Autonomous Risk Intelligence Agent

**ARIA** (Autonomous Risk Intelligence Agent) is a professional-grade AI auditing system designed to detect clinical and financial risks within corporate documents. It doesn't just read PDFs—it cross-references internal corporate claims with **live global market data** to provide a real-time risk posture.

Developed to empower analysts during placement interviews and financial reviews.

---

## 🚀 Key Features

### 🧠 Phase 1: Document Intelligence (The Brain)
- **Deep PDF Extraction**: High-precision text extraction from complex financial reports.
- **RAG Pipeline**: Uses **ChromaDB** as a local vector database to "remember" every detail of the document.
- **Llama 3.3 Integration**: Processes queries using the state-of-the-art Llama 3.3 70B model via Groq for ultra-fast, intelligent analysis.

### 🌐 Phase 2: Live Market Fusion (The Eyes)
- **Live News Integration**: Connects to **NewsAPI** to fetch headlines from the last 30 days.
- **Sentiment Analysis**: Evaluates live news to detect lawsuits, scandals, or management shifts that may not be in the PDF.
- **Risk Scoring**: Calculates a weighted score (0-100) combining internal anomalies and external sentiment.

### 📄 Phase 3: Professional Reporting (The Voice)
- **Automated PDF Generation**: Generates high-end, executive-ready PDF reports.
- **Stylized Layouts**: Includes dark-themed headers, color-coded risk indicators, and partitioned sections for Financials and News.

### 🎨 Phase 4: Premium Dashboard (The Face)
- **Modern UI**: Built with **Next.js 14**, **Tailwind CSS**, and **Framer Motion**.
- **Real-time Feedback**: Features an SSE (Server-Sent Events) progress bar showing the exact stage of analysis.
- **Glassmorphic Design**: A futuristic, dark-mode terminal aesthetic.

---

## 🛠️ Tech Stack

- **Frontend**: Next.js, TypeScript, Tailwind CSS, Lucide icons, Framer Motion.
- **Backend**: FastAPI (Python), Uvicorn.
- **AI/ML**: Groq (Llama 3.3 70B), Sentence-Transformers (Local Embeddings).
- **Database**: ChromaDB (Vector DB).
- **Utilities**: PyPDF2, NewsAPI, FPDF2.

---

## 🏃 Quick Start

### 1. Backend Setup
1. Navigate to `/backend`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Create a `.env` file with:
   ```env
   GROQ_API_KEY=your_key_here
   NEWS_API_KEY=your_key_here
   ```
4. Run the server: `python main.py`.

### 2. Frontend Setup
1. Navigate to `/frontend`.
2. Install dependencies: `npm install`.
3. Run the dashboard: `npm run dev`.
4. Open [http://localhost:3000](http://localhost:3000).

---

## 🏮 Future Roadmap & Suggestions
- [ ] **Multi-Agent Orchestration**: Use LangGraph to allow agents to "debate" over a risk score.
- [ ] **SEC Direct Sync**: Automatically pull company filings by entering a ticker symbol.
- [ ] **Email Alerts**: Integration with SendGrid to alert stakeholders when a "Critical Risk" (80+) is detected.
- [ ] **Graph Visualization**: Map out connections between subsidiaries and parent companies using Neo4j.

---

**Built with ❤️ for AI Engineering Excellence.**
