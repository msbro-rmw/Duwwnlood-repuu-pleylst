"""
helpers/hls.py — m3u8 playlist fetch + parsing.

Master playlist (multiple qualities/variants) hoti hai to har variant ka
RESOLUTION/BANDWIDTH nikal ke quality-buttons banane layak list return
karte hain. Media playlist (jisme seedhe .ts/.m4s segments hote hain,
sirf ek hi quality) ho to us case me quality-selection ki zaroorat nahi
padti — poori playlist as-is download ho jaati hai.

Important: is bot ka pura "puri playlist download karo" wala kaam yahi
hai — hum ffmpeg ko seedha m3u8 URL de dete hain, aur ffmpeg khud hi
playlist ke andar likhe SAARE segment-URLs (chahe wo hamare apne live-
system proxy ke `/api/live/<name>/seg?u=...` tokens hi kyun na hon) ek
ek karke fetch karke, connect karke, ek complete .mp4 bana deta hai.
Isse "sirf pehla segment download hoke reh jaana" wala problem solve
ho jaata hai.
"""

import re
from urllib.parse import urljoin

import aiohttp

from helpers.text_utils import display_title


async def fetch_text(url: str, headers: dict, timeout: int = 20) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=timeout) as resp:
            resp.raise_for_status()
            return await resp.text(errors="ignore")


def is_master_playlist(body: str) -> bool:
    return "#EXT-X-STREAM-INF" in body


_RES_RE = re.compile(r"RESOLUTION=(\d+)x(\d+)", re.IGNORECASE)
_BW_RE = re.compile(r"BANDWIDTH=(\d+)", re.IGNORECASE)
_NAME_RE = re.compile(r"NAME=\"([^\"]+)\"", re.IGNORECASE)


def parse_master_playlist(body: str, playlist_url: str):
    """Returns list of dicts: [{"label": "1080p", "height": 1080,
    "bandwidth": 5000000, "url": "<absolute variant m3u8 url>"}, ...]
    Sorted by quality, best first."""
    lines = body.splitlines()
    variants = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXT-X-STREAM-INF"):
            res_match = _RES_RE.search(line)
            bw_match = _BW_RE.search(line)
            name_match = _NAME_RE.search(line)
            height = int(res_match.group(2)) if res_match else None
            bandwidth = int(bw_match.group(1)) if bw_match else 0
            # Next non-comment, non-empty line is the variant URI
            j = i + 1
            variant_uri = None
            while j < len(lines):
                cand = lines[j].strip()
                if cand and not cand.startswith("#"):
                    variant_uri = cand
                    break
                j += 1
            if variant_uri:
                absolute = urljoin(playlist_url, variant_uri)
                if height:
                    label = f"{height}p"
                elif name_match:
                    label = name_match.group(1)
                else:
                    label = f"{round(bandwidth / 1000)}kbps" if bandwidth else "Auto"
                variants.append({
                    "label": label,
                    "height": height or 0,
                    "bandwidth": bandwidth,
                    "url": absolute,
                })
            i = j
        i += 1

    # De-duplicate same-label variants (keep highest bandwidth one), sort best-first
    best_by_label = {}
    for v in variants:
        cur = best_by_label.get(v["label"])
        if cur is None or v["bandwidth"] > cur["bandwidth"]:
            best_by_label[v["label"]] = v
    result = sorted(best_by_label.values(), key=lambda v: (v["height"], v["bandwidth"]), reverse=True)
    return result


async def resolve_qualities(playlist_url: str, headers: dict):
    """Playlist fetch karke decide karta hai: master (multi-quality) ya
    media (single-quality). Returns (is_master, qualities_or_none)."""
    body = await fetch_text(playlist_url, headers)
    if is_master_playlist(body):
        qualities = parse_master_playlist(body, playlist_url)
        if qualities:
            return True, qualities
    return False, None
