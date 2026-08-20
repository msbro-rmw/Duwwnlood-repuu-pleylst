"""
helpers/downloader.py — actual download engine.

HLS / DASH  -> ffmpeg ke through poori playlist (SAARE segments connect
               karke) ek single .mp4 me remux/download hoti hai.
Direct file -> seedha aiohttp streaming download (jaisa mp4/mkv links
               ke liye hota hai).
"""

import asyncio
import os

import aiohttp


class DownloadError(Exception):
    pass


def _headers_to_ffmpeg_arg(headers: dict) -> str:
    return "".join(f"{k}: {v}\r\n" for k, v in headers.items())


async def _run_ffmpeg(args: list, timeout: int = 6 * 3600) -> tuple:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-hide_banner", "-loglevel", "error", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        raise DownloadError("Download timed out (ffmpeg took too long).")
    return process.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


async def download_hls_or_dash(source_url: str, headers: dict, output_path: str) -> str:
    """m3u8/mpd URL -> poori playlist ko ek complete .mp4 me convert karta
    hai. Multiple fallback strategies (fast remux se leke re-encode audio
    tak) taaki har tarah ki playlist (TS segments / fMP4 segments) sahi se
    complete ho."""
    if os.path.exists(output_path):
        os.remove(output_path)

    ffmpeg_headers = _headers_to_ffmpeg_arg(headers)
    base_input_args = [
        "-y",
        "-headers", ffmpeg_headers,
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_on_network_error", "1",
        "-reconnect_delay_max", "5",
        "-i", source_url,
    ]

    attempts = [
        # 1) Fast remux, ADTS -> mp4 audio bitstream fix (most common case
        #    for TS-segmented HLS).
        [*base_input_args, "-c", "copy", "-bsf:a", "aac_adtstoasc",
         "-movflags", "+faststart", output_path],
        # 2) Plain copy (works well for fMP4/CMAF segments, DASH, etc.)
        [*base_input_args, "-c", "copy", "-movflags", "+faststart", output_path],
        # 3) Last resort — copy video, re-encode audio to AAC (fixes rare
        #    audio-codec edge cases without touching video quality).
        [*base_input_args, "-c:v", "copy", "-c:a", "aac",
         "-movflags", "+faststart", output_path],
    ]

    last_error = ""
    for args in attempts:
        if os.path.exists(output_path):
            os.remove(output_path)
        returncode, _stdout, stderr = await _run_ffmpeg(args)
        if returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        last_error = stderr.strip()[-800:]

    raise DownloadError(f"ffmpeg download failed.\n{last_error}")


async def download_direct_file(url: str, headers: dict, output_path: str) -> str:
    """Seedha ek video file (mp4 etc.) stream karke disk pe save karta hai."""
    if os.path.exists(output_path):
        os.remove(output_path)
    timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status >= 400:
                raise DownloadError(f"Server returned HTTP {resp.status} for this URL.")
            with open(output_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 256):
                    if chunk:
                        f.write(chunk)
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise DownloadError("Download failed — empty file received.")
    return output_path


async def probe_metadata(path: str) -> dict:
    """ffprobe se width/height/duration nikalta hai (thumbnail-free
    reply_video ke liye — bina extra photo processing library ke)."""
    args = [
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1",
        path,
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        out = stdout.decode(errors="ignore")
        width = height = 0
        duration = 0
        for line in out.splitlines():
            if line.startswith("width="):
                width = int(float(line.split("=", 1)[1]))
            elif line.startswith("height="):
                height = int(float(line.split("=", 1)[1]))
            elif line.startswith("duration="):
                try:
                    duration = int(float(line.split("=", 1)[1]))
                except ValueError:
                    duration = 0
        return {"width": width, "height": height, "duration": duration}
    except Exception:
        return {"width": 0, "height": 0, "duration": 0}
