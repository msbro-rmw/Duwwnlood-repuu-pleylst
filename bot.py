"""
bot.py — entrypoint.

Start karta hai:
  1. Ek chhota HTTP health-check server (Render Web Service port ke liye).
  2. Pyrogram Client — jo plugins/ folder se saare handlers auto-load
     karta hai (start, url_handler, callbacks, flow).
"""

import logging
import os

from pyrogram import Client

from config import Config
from helpers.healthcheck import start_healthcheck_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger("bot")


def _check_required_env():
    missing = []
    if not Config.API_ID:
        missing.append("API_ID")
    if not Config.API_HASH:
        missing.append("API_HASH")
    if not Config.BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not Config.MONGO_URI:
        missing.append("MONGO_URI")
    if missing:
        raise SystemExit(
            "❌ Missing required environment variable(s): "
            + ", ".join(missing)
            + "\nRender → Environment tab me ye set karke redeploy karo."
        )


def main():
    _check_required_env()
    os.makedirs(Config.DOWNLOAD_DIR, exist_ok=True)

    start_healthcheck_server(Config.PORT)
    logger.info(f"Health-check server started on port {Config.PORT}")

    app = Client(
        Config.SESSION_NAME,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        in_memory=True,
        plugins=dict(root="plugins"),
    )

    logger.info("Starting Video Download Bot...")
    app.run()


if __name__ == "__main__":
    main()
