"""
helpers/live_system.py — reference "live-system-final" app ke saath
shared MongoDB se seedha lecture lookup.

Jab user hume uska apna proxy-URL bhejta hai
(".../api/live/<name>/playlist"), to hum us `<name>` (jo Mongo `_id` bhi
hai) se seedha `lectures` collection me doc dhoondte hain aur uska
`original_url` (asli upstream m3u8) nikaal lete hain — proxy hit kiye
bina. Isse download zyada reliable/fast hota hai aur original video
title bhi mil jaata hai.

Agar MONGO_URI set nahi hai ya doc nahi milta, to caller apne aap
fallback kar lega (diya gaya URL hi seedha use ho jaayega).
"""

from motor.motor_asyncio import AsyncIOMotorClient

from config import Config
from helpers.text_utils import display_title

_client = None


def _get_client():
    global _client
    if _client is None and Config.MONGO_URI:
        _client = AsyncIOMotorClient(Config.MONGO_URI)
    return _client


async def lookup_lecture(name: str):
    """Returns dict {"original_url":..., "title":...} or None."""
    client = _get_client()
    if client is None:
        return None
    try:
        col = client[Config.LIVE_SYSTEM_DB_NAME][Config.LIVE_SYSTEM_COLLECTION]
        doc = await col.find_one({"_id": name})
        if not doc or not doc.get("original_url"):
            return None
        return {
            "original_url": doc["original_url"],
            "title": display_title(doc.get("title") or name),
        }
    except Exception:
        return None
