import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    return _client["finbot"]

def save_message(session_id: str, role: str, content: str):
    """Append a message to a session's chat history."""
    db = _get_db()
    db.chats.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "role":      role,
                    "content":   content,
                    "timestamp": datetime.utcnow()
                }
            },
            "$setOnInsert": {"created_at": datetime.utcnow()}
        },
        upsert=True
    )

def get_history(session_id: str, limit: int = 10) -> list[dict]:
    """Fetch the last `limit` messages for a session."""
    db  = _get_db()
    doc = db.chats.find_one({"session_id": session_id})
    if not doc:
        return []
    messages = doc.get("messages", [])
    return [
        {"role": m["role"], "content": m["content"]}
        for m in messages[-limit:]
    ]
