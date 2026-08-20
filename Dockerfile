FROM python:3.12-slim-bookworm

WORKDIR /app

# ffmpeg — HLS/DASH playlist download + remux ke liye zaroori.
# build-essential + libffi — tgcrypto (Pyrogram ka speed-up lib) compile
# karne ke liye zaroori.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    g++ \
    make \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

# Render Web Service ko ek open port chahiye hota hai health-check ke
# liye — bot.py khud ek chhota HTTP server is port par chala deta hai
# (helpers/healthcheck.py), asli kaam Telegram MTProto par hota hai.
ENV PORT=8000
EXPOSE 8000

CMD ["python3", "bot.py"]
