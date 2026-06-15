# FinBot — AI-Powered Banking Support Assistant

FinBot is a Retrieval-Augmented Generation (RAG) powered chatbot that answers banking and finance queries grounded in real policy documents. It ingests PDF knowledge bases (RBI guidelines, bank FAQs, loan policies) and provides accurate, source-cited answers through a clean chat interface.

---

## Problem Statement

Customers calling bank helplines face long wait times for answers to routine queries — EMI calculations, KYC requirements, transfer limits, or credit score guidance. FinBot solves this by providing instant, accurate, document-grounded answers 24/7.

---

## Architecture

```
User (React UI)
      │  HTTP/REST
      ▼
Flask API Gateway
      │
      ├── Query Processor (intent detection)
      │
      ▼
RAG Pipeline
  ├── Embedder      (sentence-transformers: all-MiniLM-L6-v2)
  ├── Vector Store  (ChromaDB — cosine similarity search)
  └── LLM           (Gemini 1.5 Flash — grounded answer generation)
      │
      ▼
Response Handler (format + escalation logic)
      │
      ▼
MongoDB (chat history + session persistence)
```

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | React 18, Vite                      |
| Backend     | Flask 3, Python 3.11                |
| Embeddings  | sentence-transformers (MiniLM-L6)   |
| Vector DB   | ChromaDB (persistent)               |
| LLM         | Google Gemini 1.5 Flash             |
| Database    | MongoDB Atlas                       |
| PDF Parsing | PyMuPDF (fitz)                      |
| Deployment  | Render (backend) + Vercel (frontend)|

---

## Key Features

- **RAG Pipeline** — Answers grounded strictly in uploaded knowledge documents
- **PDF Ingestion** — Admin panel to upload any banking PDF; auto-chunked and embedded
- **Escalation Logic** — Automatically flags fraud/legal queries and directs to helpline
- **Session Memory** — MongoDB stores conversation history per session
- **Source Citations** — Every answer shows which document it came from
- **Finance-Tuned Prompt** — System prompt restricts to banking domain, no hallucination

---

## Local Setup

### Backend
```bash
cd backend
cp .env.example .env        # add your GEMINI_API_KEY and MONGO_URI
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
cp .env.example .env        # set VITE_API_URL
npm install
npm run dev
```

Open `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | `/api/chat`           | Send message, get RAG answer   |
| GET    | `/api/history/:id`    | Fetch session chat history     |
| POST   | `/api/upload`         | Upload PDF to knowledge base   |
| GET    | `/api/docs`           | List ingested documents        |
| GET    | `/api/health`         | Server + vectorstore status    |

---

## License

MIT
