from dotenv import load_dotenv
load_dotenv()  # must run before importing rag, since rag reads env vars at import time

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag
import db

app = FastAPI(title="DocChat API")

# Allow the local React dev server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    question: str


@app.get("/health")
async def health():
    return {"status": "ok", "mongo_enabled": db.is_mongo_enabled()}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported right now.")

    file_bytes = await file.read()

    try:
        session_id, num_chunks = rag.create_session_from_pdf(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "session_id": session_id,
        "filename": file.filename,
        "num_chunks": num_chunks,
    }


@app.post("/chat")
async def chat(payload: ChatRequest):
    if not rag.session_exists(payload.session_id):
        raise HTTPException(status_code=404, detail="Session not found. Please upload a document first.")

    await db.save_message(payload.session_id, "user", payload.question)

    try:
        answer, sources = rag.answer_question(payload.session_id, payload.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {e}")

    await db.save_message(payload.session_id, "assistant", answer)

    return {"answer": answer, "sources": sources}


@app.get("/history/{session_id}")
async def history(session_id: str):
    messages = await db.get_history(session_id)
    return {
        "session_id": session_id,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
    }
