from pyrogram import Client, filters

import strings
from helpers import session as sess
from plugins.flow import proceed_to_quality_or_download, run_download_and_upload


@Client.on_callback_query(filters.regex(r"^name_default:"))
async def name_default_cb(bot: Client, query):
    sid = query.data.split(":", 1)[1]
    session = sess.get_session(sid)
    if not session:
        await query.answer("Ye session expire ho gaya, dobara link bhejo.", show_alert=True)
        return
    await query.answer()
    sess.update_session(sid, chosen_name=session.get("original_name"))
    await proceed_to_quality_or_download(bot, query.message, sid)


@Client.on_callback_query(filters.regex(r"^name_custom:"))
async def name_custom_cb(bot: Client, query):
    sid = query.data.split(":", 1)[1]
    session = sess.get_session(sid)
    if not session:
        await query.answer("Ye session expire ho gaya, dobara link bhejo.", show_alert=True)
        return
    await query.answer()
    sess.set_awaiting_rename(session["user_id"], sid)
    await query.message.edit_text(strings.ASK_NEW_NAME)


@Client.on_callback_query(filters.regex(r"^quality:"))
async def quality_cb(bot: Client, query):
    _, sid, idx = query.data.split(":", 2)
    session = sess.get_session(sid)
    if not session:
        await query.answer("Ye session expire ho gaya, dobara link bhejo.", show_alert=True)
        return
    qualities = session.get("qualities") or []
    try:
        chosen = qualities[int(idx)]
    except (IndexError, ValueError):
        await query.answer("Invalid quality.", show_alert=True)
        return
    await query.answer()
    sess.update_session(sid, selected_url=chosen["url"], selected_label=chosen["label"])
    await run_download_and_upload(bot, query.message, sid)
