# SpeakCast Bot — Setup Guide
## For Ranika Koneru | TEDx & Speaking Outreach Agent

---

## What you have
- `bot.py` — your full Telegram bot
- `requirements.txt` — Python dependencies
- `render.yaml` — Render deployment config

---

## Step 1 — Get your Anthropic API key
1. Go to https://console.anthropic.com
2. Sign in (create account if needed)
3. Click "API Keys" → "Create Key"
4. Copy it — you'll need it in Step 4

---

## Step 2 — Get your Telegram Chat ID
1. Open Telegram
2. Search for @userinfobot
3. Start it and type /start
4. It will show your numeric Chat ID (e.g. 123456789)
5. Copy that number

---

## Step 3 — Put your files on GitHub
1. Go to https://github.com and sign in (create free account if needed)
2. Click "New repository" → name it `speakcast-bot` → Public → Create
3. Click "uploading an existing file"
4. Upload all 3 files: bot.py, requirements.txt, render.yaml
5. Click "Commit changes"

---

## Step 4 — Deploy on Render
1. Go to https://render.com and sign in with GitHub
2. Click "New +" → "Blueprint" → connect your speakcast-bot repo
3. Render will read render.yaml automatically
4. You'll be asked to fill in 3 environment variables:

   TELEGRAM_TOKEN    → 8665600327:AAEUv4wq9dSX8J1KKHCp1b1xJsOa9bqNUQo
   ANTHROPIC_API_KEY → (from Step 1)
   ALLOWED_CHAT_ID   → (your chat ID from Step 2)

5. Click "Apply" — Render will build and start your bot

---

## Step 5 — Test it!
1. Open Telegram → find @SpeakCastbot
2. Type /start
3. Try /tedx or /podcasts

---

## Your bot's commands
/start     — Welcome message
/tedx      — Find open TEDx applications
/podcasts  — Find podcasts to pitch this week  
/trends    — Trending wellness topics to use in outreach
/pitch     — Draft a personalized outreach email
/duo       — Find joint opportunities for you + Dr. Claud
/briefing  — On-demand daily briefing
/clear     — Fresh conversation start

Daily briefing fires automatically at 8am UTC (9am Amsterdam / 3am EST)
To change the time, edit line in bot.py: datetime.strptime("08:00", "%H:%M")

---

## Need help?
Email: ranika.koneru@gmail.com (that's you!)
Bot username: @SpeakCastbot
