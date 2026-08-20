import os

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import strings
from config import Config
from database import db
from helpers import session as sess
from helpers.downloader import (
    DownloadError,
    download_direct_file,
    download_hls_or_dash,
    probe_metadata,
)
from helpers.text_utils import html_escape, safe_filename


async def proceed_to_quality_or_download(bot, status_message, sid: str):
    """Naam decide ho chuka hai — ab quality poochni hai (agar multiple
    available hain) warna seedha download shuru kar do."""
    session = sess.get_session(sid)
    if not session:
        return

    qualities = session.get("qualities")
    if qualities and len(qualities) > 1:
        buttons = []
        for idx, q in enumerate(qualities):
            buttons.append([InlineKeyboardButton(f"🎬 {q['label']}", callback_data=f"quality:{sid}:{idx}")])
        try:
            await status_message.edit_text(strings.SELECT_QUALITY_TEXT, reply_markup=InlineKeyboardMarkup(buttons))
        except Exception:
            await bot.send_message(
                chat_id=session["chat_id"],
                text=strings.SELECT_QUALITY_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        return

    # Sirf ek hi quality available hai (ya koi quality-list hai hi nahi,
    # jaise direct file / single-rendition playlist) -> seedha download.
    selected_url = qualities[0]["url"] if qualities else session["source_url"]
    sess.update_session(sid, selected_url=selected_url)
    await run_download_and_upload(bot, status_message, sid)


async def run_download_and_upload(bot, status_message, sid: str):
    session = sess.get_session(sid)
    if not session:
        return

    chat_id = session["chat_id"]
    user_id = session["user_id"]
    selected_url = session.get("selected_url") or session["source_url"]
    headers = session["headers"]
    kind = session["kind"]
    name = session.get("chosen_name") or session.get("original_name") or "video"

    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)
    output_path = os.path.join(Config.DOWNLOAD_DIR, f"{user_id}_{sid}_{safe_filename(name)}.mp4")

    try:
        await status_message.edit_text(strings.DOWNLOADING)
    except Exception:
        status_message = await bot.send_message(chat_id=chat_id, text=strings.DOWNLOADING)

    try:
        if kind in ("hls", "dash"):
            await download_hls_or_dash(selected_url, headers, output_path)
        else:
            await download_direct_file(selected_url, headers, output_path)
    except DownloadError as e:
        await status_message.edit_text(strings.DOWNLOAD_FAILED.format(error=str(e)[:500]))
        _cleanup(output_path)
        sess.drop_session(sid)
        return
    except Exception as e:
        await status_message.edit_text(strings.DOWNLOAD_FAILED.format(error=str(e)[:500]))
        _cleanup(output_path)
        sess.drop_session(sid)
        return

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    if file_size == 0:
        await status_message.edit_text(strings.DOWNLOAD_FAILED.format(error="Empty file — download incomplete."))
        _cleanup(output_path)
        sess.drop_session(sid)
        return

    if file_size > Config.MAX_UPLOAD_BYTES:
        size_str = f"{file_size / (1024 * 1024):.1f} MB"
        await status_message.edit_text(strings.FILE_TOO_LARGE.format(size=size_str))
        _cleanup(output_path)
        sess.drop_session(sid)
        return

    await status_message.edit_text(strings.DOWNLOAD_DONE)

    try:
        meta = await probe_metadata(output_path)
        index = await db.next_download_index(user_id)
        caption = strings.build_caption(index, html_escape(name), Config.UPLOAD_CREDIT)

        await bot.send_video(
            chat_id=chat_id,
            video=output_path,
            caption=caption,
            width=meta["width"] or None,
            height=meta["height"] or None,
            duration=meta["duration"] or None,
            supports_streaming=True,
        )
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=strings.UPLOAD_FAILED.format(error=str(e)[:500]))
    finally:
        _cleanup(output_path)
        sess.drop_session(sid)


def _cleanup(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
