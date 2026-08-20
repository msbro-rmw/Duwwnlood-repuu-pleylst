import re

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import strings
from config import Config
from database import db
from helpers import session as sess
from helpers.detect import match_live_system_url, sniff_url_type
from helpers.hls import resolve_qualities
from helpers.live_system import lookup_lecture
from helpers.text_utils import guess_name_from_url

URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)


def _extract_url(text: str) -> str:
    m = URL_REGEX.search(text or "")
    return m.group(0).strip() if m else ""


@Client.on_message(filters.text & filters.private & ~filters.command(["start"]))
async def text_dispatcher(bot: Client, message):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    # 1) Agar user "Rename" tap karke naya naam bhejne wala hai
    sid = sess.pop_awaiting_rename(user_id)
    if sid:
        await _handle_new_name(bot, message, sid, text)
        return

    # 2) Agar message me URL hai -> naya download flow shuru karo
    url = _extract_url(text)
    if url:
        await _handle_new_url(bot, message, url)
        return

    # 3) Kuch aur text -> link bhejne ka reminder
    await message.reply_text(strings.ASK_SEND_URL)


async def _handle_new_url(bot: Client, message, url: str):
    user = message.from_user
    await db.ensure_user(user.id, user.first_name or "", user.username or "")

    status_msg = await message.reply_text(strings.PROCESSING)

    try:
        source_url = url
        original_name = guess_name_from_url(url)
        is_pw = False

        lecture_name = match_live_system_url(url)
        if lecture_name:
            is_pw = True
            doc = await lookup_lecture(lecture_name)
            if doc:
                source_url = doc["original_url"]
                original_name = doc["title"] or original_name
            # doc na mile to bhi is_pw True rehta hai (proxy URL hi hai),
            # source_url wahi original diya hua URL rahega (fallback).

        headers = Config.PW_HEADERS if is_pw else Config.GENERIC_HEADERS

        if lecture_name:
            url_type = "hls"
        else:
            url_type = await sniff_url_type(source_url, headers)

        qualities = None
        if url_type == "hls":
            try:
                is_master, parsed_qualities = await resolve_qualities(source_url, headers)
                if is_master:
                    qualities = parsed_qualities
            except Exception:
                # Playlist fetch fail hui to bhi hum ffmpeg ko seedha try
                # karne dete hain (single/"Original" quality maan ke).
                qualities = None

        sid = sess.new_session(
            user.id,
            url=url,
            source_url=source_url,
            kind=url_type,
            headers=headers,
            original_name=original_name,
            chosen_name=None,
            qualities=qualities,
            chat_id=message.chat.id,
        )

        await status_msg.delete()

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(strings.BTN_RENAME, callback_data=f"name_custom:{sid}"),
            InlineKeyboardButton(strings.BTN_DEFAULT, callback_data=f"name_default:{sid}"),
        ]])
        await bot.send_message(
            chat_id=message.chat.id,
            text=strings.SET_NAME_TEXT.format(original_name=original_name),
            reply_markup=buttons,
        )
    except Exception as e:
        try:
            await status_msg.edit_text(strings.INVALID_URL.format(reason=str(e)[:300]))
        except Exception:
            await message.reply_text(strings.INVALID_URL.format(reason=str(e)[:300]))


async def _handle_new_name(bot: Client, message, sid: str, new_name: str):
    session = sess.get_session(sid)
    if not session:
        await message.reply_text(strings.ASK_SEND_URL)
        return
    new_name = new_name.strip()
    if not new_name:
        await message.reply_text(strings.ASK_NEW_NAME)
        sess.set_awaiting_rename(session["user_id"], sid)
        return

    sess.update_session(sid, chosen_name=new_name)
    saved_msg = await message.reply_text(strings.NAME_SAVED.format(name=new_name))

    from plugins.flow import proceed_to_quality_or_download
    await proceed_to_quality_or_download(bot, saved_msg, sid)
