"""
Chat history storage.

If MONGO_URI is set in .env, chat history is persisted in MongoDB.
Otherwise, it falls back to a simple in-memory store (data lost on restart,
but perfectly fine for local dev / demoing the project).
"""
import os
import time
from typing import List, Dict

MONGO_URI = os.getenv("MONGO_URI", "").strip()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "docchat")

_in_memory_store: Dict[str, List[Dict]] = {}
_mongo_client = None
_mongo_collection = None

if MONGO_URI:
    from motor.motor_asyncio import AsyncIOMotorClient

    _mongo_client = AsyncIOMotorClient(MONGO_URI)
    _mongo_collection = _mongo_client[MONGO_DB_NAME]["chat_messages"]


async def save_message(session_id: str, role: str, content: str) -> None:
    """Persist a single chat message (role = 'user' or 'assistant')."""
    entry = {"session_id": session_id, "role": role, "content": content, "ts": time.time()}

    if _mongo_collection is not None:
        await _mongo_collection.insert_one(entry)
    else:
        _in_memory_store.setdefault(session_id, []).append(entry)


async def get_history(session_id: str) -> List[Dict]:
    """Return chat history for a session, oldest first."""
    if _mongo_collection is not None:
        cursor = _mongo_collection.find({"session_id": session_id}).sort("ts", 1)
        return [doc async for doc in cursor]
    return _in_memory_store.get(session_id, [])


def is_mongo_enabled() -> bool:
    return _mongo_collection is not None
