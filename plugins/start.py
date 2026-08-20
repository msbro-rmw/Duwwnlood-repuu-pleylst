from pyrogram import Client, filters

import strings
from database import db


@Client.on_message(filters.command("start") & filters.private)
async def start_handler(bot: Client, message):
    user = message.from_user
    await db.ensure_user(user.id, user.first_name or "", user.username or "")
    await message.reply_text(
        strings.WELCOME_TEXT.format(mention=user.mention),
    )
