"""
helpers/session.py — ek chhota in-memory state-machine har user ke
"link bhejo -> naam set karo -> quality chuno -> download+upload" flow
ko track karne ke liye.

Note: ye state process-memory me rehta hai (DB me nahi) — kyunki ye
sirf ek chalu conversation ka temporary step hai, permanent data nahi.
Agar bot restart ho jaaye beech me to us particular pending download ko
user ko dobara link bhejna padega — ye normal/expected behaviour hai.
"""

import time
import uuid

SESSIONS: dict = {}
AWAITING_RENAME: dict = {}  # user_id -> session_id


def new_session(user_id: int, **fields) -> str:
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = {
        "user_id": user_id,
        "created_at": time.time(),
        **fields,
    }
    return sid


def get_session(sid: str):
    return SESSIONS.get(sid)


def update_session(sid: str, **fields):
    if sid in SESSIONS:
        SESSIONS[sid].update(fields)


def drop_session(sid: str):
    SESSIONS.pop(sid, None)


def set_awaiting_rename(user_id: int, sid: str):
    AWAITING_RENAME[user_id] = sid


def pop_awaiting_rename(user_id: int):
    return AWAITING_RENAME.pop(user_id, None)


def is_awaiting_rename(user_id: int) -> bool:
    return user_id in AWAITING_RENAME


def cleanup_stale_sessions(max_age_seconds: int = 6 * 3600):
    now = time.time()
    stale = [sid for sid, s in SESSIONS.items() if now - s.get("created_at", now) > max_age_seconds]
    for sid in stale:
        SESSIONS.pop(sid, None)
