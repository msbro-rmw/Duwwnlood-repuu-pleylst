"""
config.py — Saari settings sirf environment variables se aati hain.
Render.com pe Environment tab me ye variables set karne hai (README.md
me poori list + example values di gayi hai).
"""

import os


def _int(name: str, default: int) -> int:
    val = os.environ.get(name, "")
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


class Config:
    # ── Telegram Bot (Pyrogram / MTProto) ────────────────────────────────
    API_ID = _int("API_ID", 0)
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    SESSION_NAME = os.environ.get("SESSION_NAME", "video_download_bot")

    # Owner / admin (optional — sirf logging/broadcast type future use ke liye)
    OWNER_ID = _int("OWNER_ID", 0)

    # ── MongoDB ───────────────────────────────────────────────────────────
    # Same MONGO_URI jo "live-system-final" (player/proxy) app use karta hai
    # — taaki "/api/live/<name>/playlist" jaisa URL aane par hum seedha
    # us lecture ka `original_url` DB se read kar sakein (proxy hit kiye
    # bina — zyada reliable + fast full-video download).
    MONGO_URI = os.environ.get("MONGO_URI", "")

    # Us live-system ka DB naam (jaha "lectures" collection padhi jaati hai).
    LIVE_SYSTEM_DB_NAME = os.environ.get("LIVE_SYSTEM_DB_NAME", "pw_live_system")
    LIVE_SYSTEM_COLLECTION = os.environ.get("LIVE_SYSTEM_COLLECTION", "lectures")

    # Is download-bot ki apni data (users + per-user index counter) — same
    # cluster, alag database — taaki live-system ka data kabhi touch na ho.
    BOT_DB_NAME = os.environ.get("BOT_DB_NAME", "video_download_bot_db")

    # ── Download / Upload behaviour ─────────────────────────────────────
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads")

    # Telegram bot accounts (via MTProto/Pyrogram, NOT the 50MB HTTP Bot
    # API limit) can upload up to ~2000MB. Thoda buffer rakh ke limit.
    MAX_UPLOAD_BYTES = _int("MAX_UPLOAD_BYTES", 1950 * 1024 * 1024)

    # Caption me fixed credit line
    UPLOAD_CREDIT = os.environ.get("UPLOAD_CREDIT", "@SmartBoy_ApnaMS")

    # ── Web server (Render Web Service ke liye — sirf port open rakhne ke
    #    liye, health check pass karne ke liye; koi real functionality
    #    yaha nahi hai) ────────────────────────────────────────────────
    PORT = _int("PORT", 8000)

    # ── ffmpeg / HLS fetch headers (PW/PhysicsWallah live-system ke liye
    #    zaroori — CDN Referer/Origin check karta hai) ───────────────────
    PW_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.pw.live/",
        "Origin": "https://www.pw.live",
    }
    GENERIC_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
