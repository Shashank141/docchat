# DocChat — AI Document Q&A Assistant

Upload a PDF, ask questions about it, get grounded answers. Built as a full-stack
demo covering: React frontend, FastAPI backend, LangChain RAG pipeline, and
MongoDB-backed chat history.

**Stack:** React + Tailwind · FastAPI · LangChain · HuggingFace embeddings (local) ·
FAISS vector search · OpenAI (gpt-4o-mini) · MongoDB (optional)

---

## How it works

1. You upload a PDF → backend extracts text, splits it into chunks, embeds the
   chunks locally (HuggingFace `all-MiniLM-L6-v2`, no API key needed for this part),
   and stores them in an in-memory FAISS index for that session.
2. You ask a question → backend embeds the question, retrieves the most relevant
   chunks, and sends them + your question to OpenAI's `gpt-4o-mini` via LangChain
   to generate an answer grounded in the document.
3. Every message is saved via `db.py` — to MongoDB if you configure `MONGO_URI`,
   otherwise to a simple in-memory store (fine for local testing).

---

## 1. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (get one at platform.openai.com/api-keys)
# MONGO_URI is optional — leave blank to skip Mongo and use in-memory history

uvicorn main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Check `http://localhost:8000/health`.

> First request after starting the server will be slow — it downloads the
> HuggingFace embedding model (~90MB) once, then caches it.

## 2. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`. Open it, upload a PDF, and start asking questions.

---

## Enabling MongoDB (optional)

By default, chat history lives in memory and resets when the backend restarts —
totally fine for demoing. To persist it:

1. Run MongoDB locally (`mongod`) or create a free MongoDB Atlas cluster.
2. Set `MONGO_URI` in `backend/.env`, e.g.:
   ```
   MONGO_URI=mongodb://localhost:27017
   ```
3. Restart the backend. Check `/health` — it should report `"mongo_enabled": true`.

---

## Project structure

```
docchat/
├── backend/
│   ├── main.py          # FastAPI app: /upload, /chat, /history endpoints
│   ├── rag.py           # PDF chunking, embeddings, FAISS, LangChain RAG logic
│   ├── db.py            # MongoDB / in-memory chat history storage
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx      # Upload UI + chat interface
    │   ├── main.jsx
    │   └── index.css
    ├── package.json
    └── tailwind.config.js
```


