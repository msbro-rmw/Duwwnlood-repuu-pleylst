# Video Download Bot

Telegram bot jo koi bhi video link (`.mp4`, `.mpd`/DASH, `.m3u8`/HLS —
including apne **live-system-final** proxy app ka `/api/live/<name>/playlist`
URL) accept karta hai aur poora video download karke, user ke choose kiye
naam/quality ke saath, Telegram par **as video** (kabhi bhi document nahi)
bhej deta hai.

## Flow

1. `/start` → welcome message, link maangta hai.
2. User koi bhi video/playlist URL bhejta hai.
   - Bot pehle check karta hai: kya ye humare apne live-system-final app
     ka `/api/live/<name>/playlist` URL hai? Agar haan, to seedha shared
     MongoDB (`lectures` collection) se us lecture ka **asli** `original_url`
     + title uthata hai (proxy hit kiye bina — zyada reliable).
   - Warna, URL ka content-type/extension check karke decide karta hai:
     HLS (`m3u8`) / DASH (`mpd`) / direct file.
3. `Processing Your Link time...⏳` dikhta hai, delete hoke ek naam-selection
   message aata hai (`Original name` + `🖊️ Rename` / `📝 Default` buttons).
4. Naam decide hone ke baad — agar HLS master-playlist hai (multiple
   qualities available) to quality-selection buttons aate hain; warna
   seedha download shuru ho jaata hai.
5. `Wait im Downloading Please Wait...🤭` → ffmpeg poori playlist (SAARE
   segments connect karke) ek complete `.mp4` bana deta hai (ya direct
   file stream-download hoti hai).
6. `DONE ✅ ...` → video Telegram par **as video** (supports_streaming)
   bheja jaata hai, caption:

   ```
   {index}📝 Titel: {name}

   📥 Upload By♠: @SmartBoy_ApnaMS
   ```

   `{index}` har user ka apna badhta hua counter hai (MongoDB me store hota
   hai).

## Structure

```
Downloadrepo/
├── bot.py                  # entrypoint (Pyrogram Client + health server)
├── config.py                # saari settings env vars se
├── strings.py                # saare bot messages
├── requirements.txt
├── Dockerfile
├── .env.example
├── database/
│   └── db.py                 # bot ki apni Mongo (users + index counter)
├── helpers/
│   ├── text_utils.py          # title/filename cleanup
│   ├── detect.py               # URL type detection (hls/dash/direct)
│   ├── hls.py                   # m3u8 fetch + master-playlist quality parsing
│   ├── downloader.py             # ffmpeg (HLS/DASH) + aiohttp (direct) downloader
│   ├── live_system.py             # shared MongoDB "lectures" lookup
│   ├── session.py                  # in-memory rename/quality state machine
│   └── healthcheck.py               # Render Web Service ke liye tiny HTTP server
├── plugins/                          # Pyrogram auto-loads is folder ko
│   ├── start.py                       # /start
│   ├── url_handler.py                  # link intake + naya naam capture
│   ├── callbacks.py                     # Rename/Default/Quality buttons
│   └── flow.py                           # quality-step + download+upload runner
└── downloads/                             # runtime scratch dir (auto-created)
```

## Environment Variables (Render → Environment tab)

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | my.telegram.org se |
| `API_HASH` | ✅ | my.telegram.org se |
| `BOT_TOKEN` | ✅ | @BotFather se naya bot banao |
| `MONGO_URI` | ✅ | Same connection string jo live-system-final app use karta hai |
| `LIVE_SYSTEM_DB_NAME` | ❌ | default `pw_live_system` |
| `LIVE_SYSTEM_COLLECTION` | ❌ | default `lectures` |
| `BOT_DB_NAME` | ❌ | default `video_download_bot_db` (is bot ka apna alag DB) |
| `DOWNLOAD_DIR` | ❌ | default `./downloads` |
| `MAX_UPLOAD_BYTES` | ❌ | default ~1.95GB |
| `UPLOAD_CREDIT` | ❌ | default `@SmartBoy_ApnaMS` |
| `OWNER_ID` | ❌ | reserved for future admin features |
| `PORT` | ❌ | default `8000` — Render Web Service ke liye |

Poori list `.env.example` file me bhi hai.

## Deploy (Render.com — Web Service, Docker)

1. Is repo ko GitHub par push karo.
2. Render → New → Web Service → apna repo select karo → **Environment: Docker**.
3. Upar wali saari Environment Variables set karo.
4. Port **8000** hi rakhna (`.env.example` me default already 8000 hai —
   Dockerfile bhi `EXPOSE 8000` karta hai).
5. Deploy — logs me `Starting Video Download Bot...` dikhte hi bot live hai.

## Notes

- Upload mode hamesha **video** hai — koi "as document" setting nahi hai
  (jaisa ki manga gaya tha), sirf quality user choose kar sakta hai.
- Naam/rename session process-memory me rehta hai — agar bot beech me
  restart ho jaaye to us particular pending download ka link dobara
  bhejna padega (permanent user data — jaise download counter — Mongo me
  hi safe rehta hai).
- HLS/DASH download ffmpeg se hota hai (`-c copy` remux, fallback chain
  audio-codec edge cases ke liye) — koi re-encode nahi (fast + original
  quality retain).
