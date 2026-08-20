"""
helpers/detect.py — kis type ka URL hai ye pata karna:
  - "hls"    -> .m3u8 / application/vnd.apple.mpegurl
  - "dash"   -> .mpd  / application/dash+xml
  - "direct" -> seedha video file (mp4, mkv, etc.)

Plus: humare apne "live-system-final" player/proxy app ka special
`/api/live/<name>/playlist` pattern pehchanna (taaki us case me MongoDB
se seedha `original_url` uthaya ja sake).
"""

import re
from urllib.parse import urlparse

import aiohttp

LIVE_SYSTEM_PATTERN = re.compile(r"/api/live/([^/]+)/playlist/?$")


def match_live_system_url(url: str):
    """Agar URL humare apne live-system-final app ka playlist-endpoint hai
    to us lecture ka `name` (Mongo `_id`) return karta hai, warna None."""
    try:
        path = urlparse(url).path
    except Exception:
        return None
    m = LIVE_SYSTEM_PATTERN.search(path)
    return m.group(1) if m else None


async def sniff_url_type(url: str, headers: dict, timeout: int = 15) -> str:
    """Extension se pehle try karo (fast path), warna Content-Type sniff
    karke pata lagao."""
    path = urlparse(url).path.lower()
    if path.endswith(".m3u8"):
        return "hls"
    if path.endswith(".mpd"):
        return "dash"
    if path.endswith((".mp4", ".mkv", ".webm", ".mov", ".avi", ".ts", ".flv")):
        return "direct"

    # Content-Type sniff — chhota GET (kuch bytes) taaki bina extension
    # wale URLs (jaise humara apna live-system `/playlist` endpoint) bhi
    # sahi se detect ho jaayein.
    try:
        async with aiohttp.ClientSession() as session:
            req_headers = dict(headers)
            req_headers["Range"] = "bytes=0-2047"
            async with session.get(url, headers=req_headers, timeout=timeout) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                if "mpegurl" in ctype or "m3u8" in ctype:
                    return "hls"
                if "dash+xml" in ctype:
                    return "dash"
                return "direct"
    except Exception:
        # Fetch fail ho jaaye to bhi generic "direct" maan ke aage badho —
        # actual download step apni error handling khud karega.
        return "direct"
