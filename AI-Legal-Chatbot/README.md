# Dharma Legal Chatbot

> AI-powered legal guidance for Indian police complaint procedures and citizens' rights.

## Architecture

```
Dharma Chatbot
├── AI-Legal-Chatbot/
│   ├── src/
│   │   ├── preprocessing/     ✅ PDF extraction, cleaning, chunking, metadata
│   │   ├── embedding/         ✅ BAAI/bge-large-en-v1.5 + FAISS index builder
│   │   ├── retrieval/         ✅ Similarity search + RAG prompt builder
│   │   ├── llm/               ✅ Ollama client + RAG response generator
│   │   ├── chatbot/           ✅ Intent classifier, follow-up logic, orchestrator
│   │   └── api/               ✅ FastAPI backend (port 8000)
│   ├── data/
│   │   ├── chunks/            7 legal document chunk files
│   │   ├── metadata/          Flat metadata JSON (1946 chunks)
│   │   └── vector_db/         FAISS index + metadata pickle
│   └── frontend/              ✅ React/Vite premium UI (port 5173)
└── start.bat                  One-click startup script
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai) installed with a model

### 1. Install Ollama and pull a model
```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull llama3  # or: mistral, llama3.2, etc.
```

### 2. Install Python dependencies
```bash
# From the Dharma Chatbot root
.venv\Scripts\pip install -r AI-Legal-Chatbot\requirements.txt
```

### 3. Install frontend dependencies
```bash
cd AI-Legal-Chatbot\frontend
npm install
```

### 4. Build the FAISS index (first time only)
```bash
cd AI-Legal-Chatbot
..\\.venv\Scripts\python -m src.embedding.build_vector_db
```

### 5. Start everything
```bash
# Windows — run from the Dharma Chatbot root:
start.bat

# Or manually in two terminals:
# Terminal 1 (Backend):
cd AI-Legal-Chatbot
..\\.venv\Scripts\python -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2 (Frontend):
cd AI-Legal-Chatbot\frontend
npm run dev
```

Open: **http://localhost:5173**

## Supported Complaint Categories
| Category | Keywords |
|---|---|
| 🔓 Theft / Robbery | theft, stolen, robbed, burglary |
| 💻 Cybercrime / Fraud | online fraud, UPI fraud, hacked |
| 🏠 Domestic Violence | domestic abuse, dowry, cruelty |
| 🚗 Traffic Accident | accident, hit and run, rash driving |
| 🛍️ Consumer Dispute | product defect, refund, consumer court |
| 👤 Missing Person | missing person, kidnapping, abducted |
| 📋 RTI | right to information, government record |

## Legal Knowledge Base
| Document | Type |
|---|---|
| Bharatiya Nagarik Suraksha Sanhita (BNSS) | Criminal Procedure |
| Bharatiya Nyaya Sanhita (BNS) | Criminal Law |
| Bharatiya Sakshya Adhiniyam 2023 | Evidence Law |
| Consumer Protection Act 2019 | Consumer Law |
| Information Technology Act 2000 | Cyber Law |
| Motor Vehicles Act 1988 | Traffic Law |
| Right to Information Act 2005 | Administrative Law |

## API Endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | System health check |
| POST | `/api/chat` | Send a message, get legal guidance |
| GET | `/api/session/{id}` | Get conversation history |
| DELETE | `/api/session/{id}` | Clear a session |
| GET | `/docs` | Interactive API documentation |

## ⚠️ Disclaimer
This tool provides **general legal information only** and does not constitute legal advice. For your specific situation, please consult a qualified lawyer or visit your nearest Legal Services Authority.
