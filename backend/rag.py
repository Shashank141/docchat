"""
Core RAG (Retrieval-Augmented Generation) logic for DocChat.

Flow:
1. A PDF is uploaded -> extract text -> split into chunks.
2. Chunks are embedded (HuggingFace sentence-transformers, runs locally, no API key needed)
   and stored in an in-memory FAISS vector index, one index per session.
3. On a chat question, we embed the question, retrieve the most relevant chunks,
   and pass them + the question to a Groq-hosted LLM (free tier) via LangChain
   to generate a grounded answer.
"""
import io
import uuid
from typing import Dict, Tuple, List

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.schema import Document

# Loaded once, reused across requests/sessions (this is the slow part on first run,
# since it downloads the embedding model the very first time).
_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# session_id -> FAISS vector store for that document
_session_stores: Dict[str, FAISS] = {}
# session_id -> original filename, just for display
_session_filenames: Dict[str, str] = {}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def create_session_from_pdf(file_bytes: bytes, filename: str) -> Tuple[str, int]:
    """Chunk + embed a PDF's text, store it, and return (session_id, num_chunks)."""
    text = extract_text_from_pdf(file_bytes)
    if not text.strip():
        raise ValueError("Could not extract any text from this PDF (it may be scanned/image-only).")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_text(text)

    docs = [Document(page_content=chunk, metadata={"chunk_index": i}) for i, chunk in enumerate(chunks)]

    vector_store = FAISS.from_documents(docs, _embeddings)

    session_id = str(uuid.uuid4())
    _session_stores[session_id] = vector_store
    _session_filenames[session_id] = filename

    return session_id, len(chunks)


def session_exists(session_id: str) -> bool:
    return session_id in _session_stores


def get_filename(session_id: str) -> str:
    return _session_filenames.get(session_id, "document")


def answer_question(session_id: str, question: str, k: int = 4) -> Tuple[str, List[str]]:
    """Retrieve relevant chunks for the question and generate a grounded answer."""
    if session_id not in _session_stores:
        raise ValueError("Unknown session_id. Upload a document first.")

    vector_store = _session_stores[session_id]
    relevant_docs = vector_store.similarity_search(question, k=k)
    context = "\n\n---\n\n".join(doc.page_content for doc in relevant_docs)
    sources = [doc.page_content[:200] for doc in relevant_docs]

    prompt = f"""You are a helpful assistant answering questions about a specific document.
Use ONLY the context below to answer. If the answer isn't in the context, say you don't know
based on the document — do not make things up.

Context from the document:
{context}

Question: {question}

Answer:"""

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)
    response = llm.invoke(prompt)

    return response.content, sources
