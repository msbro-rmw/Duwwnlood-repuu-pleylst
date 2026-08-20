"""
helpers/text_utils.py — title / filename cleanup helpers.

display_title() is the SAME conversion logic used by the reference
"live-system-final" app (utils/text.py) — jab humein us system ke slug
(`_id`) se ek readable title banana ho (hyphen/underscore -> space).
"""

import os
import re
import unicodedata
from urllib.parse import unquote, urlparse


def display_title(name: str) -> str:
    """Slug jaisa naam (e.g. 'Shivam-Mishra-Sir-live-class') ko readable
    title me convert karta hai ('Shivam Mishra Sir live class')."""
    if not name:
        return ""
    title = re.sub(r"[-_]+", " ", str(name))
    title = re.sub(r"\s+", " ", title).strip()
    return title


def guess_name_from_url(url: str) -> str:
    """Kisi bhi generic video URL se ek reasonable display name nikalta hai
    (query string hata ke, extension hata ke, %20 jaise encoding decode
    karke)."""
    try:
        parsed = urlparse(url)
        base = os.path.basename(parsed.path)
        base = unquote(base)
        if not base:
            base = parsed.netloc or "video"
        name, _ext = os.path.splitext(base)
        name = name.strip() or "video"
        return display_title(name) if ("-" in name or "_" in name) else name
    except Exception:
        return "video"


def safe_filename(name: str) -> str:
    """Filesystem ke liye safe filename — koi bhi language allow (Hindi
    included), sirf OS ke liye problematic characters hata di jaati hain.
    NO LENGTH LIMIT jaisa user chahte hain, bas ek reasonable cap taaki
    filesystem error na aaye."""
    name = (name or "video").strip()
    cleaned = []
    for ch in name:
        if ch in ('/', '\\', '\0'):
            cleaned.append(" ")
        elif ch in (':', '*', '?', '"', '<', '>', '|'):
            cleaned.append(" ")
        else:
            cleaned.append(ch)
    cleaned_name = "".join(cleaned)
    cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()
    if not cleaned_name:
        cleaned_name = "video"
    # Filesystem safety cap (Telegram / OS filename length limits)
    return cleaned_name[:200]


def html_escape(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
