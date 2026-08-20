"""
database/db.py — is bot ki apni MongoDB (users + har user ka apna
download-index counter, jo caption me "{n}📝 Titel: ..." wale number ke
liye use hota hai).

Same MONGO_URI use hota hai jo live-system app use karta hai, lekin
ALAG database (Config.BOT_DB_NAME) me — taaki live-system ka data kabhi
touch/overwrite na ho.
"""

import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from config import Config

_client = None
_users_col = None


def _init():
    global _client, _users_col
    if _client is None:
        if not Config.MONGO_URI:
            raise RuntimeError(
                "MONGO_URI env var set nahi hai — is bot ko chalane ke liye "
                "MongoDB connection string zaroori hai."
            )
        _client = AsyncIOMotorClient(Config.MONGO_URI)
        _users_col = _client[Config.BOT_DB_NAME]["users"]
    return _users_col


async def ensure_user(user_id: int, first_name: str = "", username: str = ""):
    col = _init()
    await col.update_one(
        {"_id": user_id},
        {
            "$setOnInsert": {
                "_id": user_id,
                "first_name": first_name,
                "username": username,
                "joined_at": datetime.datetime.utcnow(),
                "download_count": 0,
            }
        },
        upsert=True,
    )


async def next_download_index(user_id: int) -> int:
    """Is user ka agla download-index number atomically badha ke return
    karta hai (1, 2, 3, ... — caption ke liye)."""
    col = _init()
    doc = await col.find_one_and_update(
        {"_id": user_id},
        {"$inc": {"download_count": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["download_count"]


async def total_users() -> int:
    col = _init()
    return await col.count_documents({})
