# strings.py — bot ke saare messages ek jagah.
# Jo texts user ne exactly diye the, unhe hu-baa-hu rakha gaya hai.

WELCOME_TEXT = (
    "👋 **Namaste {mention}!**\n\n"
    "Main ek **Video Download Bot** hoon 🎬\n\n"
    "Mujhe koi bhi video ka link bhejo — **mp4 / m3u8 (HLS) / mpd (DASH)** "
    "kisi bhi type ka URL chalega, main use download karke tumhe seedha "
    "yahi Telegram par bhej dunga.\n\n"
    "📎 Bas mujhe link bhejo, aage ka sab main sambhal lunga 👇"
)

ASK_SEND_URL = "📎 Ab mujhe apna video/playlist ka **link bhejo**."

PROCESSING = "Processing Your Link time...⏳"

INVALID_URL = (
    "❌ Ye link process nahi ho paya.\n\n"
    "Reason: `{reason}`\n\n"
    "Kripya sahi video/playlist link bhejein."
)

SET_NAME_TEXT = (
    "**Set Video Name**\n\n"
    "**Original name:** `{original_name}`"
)

BTN_RENAME = "🖊️ Rename"
BTN_DEFAULT = "📝 Default"

ASK_NEW_NAME = "🖊️ Theek hai, ab video ka **naya naam** bhejo (koi bhi language/length chalegi):"

NAME_SAVED = "✅ Naam save ho gaya: `{name}`"

SELECT_QUALITY_TEXT = "🎚️ **Select Quality**\n\nNeeche di gayi qualities me se ek chuno:"

DOWNLOADING = "Wait im Downloading Please Wait...🤭"

DOWNLOAD_DONE = (
    "DONE ✅ \n\n"
    "I downloaded Your Video \n\n"
    "Thank you for using me send me more link to download 💜."
)

UPLOADING = "📤 Uploading your video to Telegram..."

FILE_TOO_LARGE = (
    "⚠️ Ye video Telegram par bhejne ke liye bahut badi hai "
    "({size}).\n\nKripya koi choti quality chuno."
)

DOWNLOAD_FAILED = "❌ Download nahi ho paya.\n\n`{error}`"

UPLOAD_FAILED = "❌ Upload nahi ho paya.\n\n`{error}`"


def build_caption(index: int, name: str, credit: str) -> str:
    return f"<b>{index}📝 Titel: {name}\n\n📥 Upload By♠: {credit}</b>"
