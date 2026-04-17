import os
import anthropic
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_CHAT_ID = os.environ.get("ALLOWED_CHAT_ID")
WEBHOOK_URL = "https://speakcast-agent-production.up.railway.app"
PORT = 8443

# ── Ranika & Dr. Claud's full profile ────────────────────────────────────────
SYSTEM_PROMPT = """You are the personal research and outreach AI agent for Ranika Koneru and Dr. Claud van Oijen.

=== RANIKA KONERU ===
Title: Operator | Speaker | Wellness Architect
Companies: Co-Founder, Evolve Weight & Wellness (2 US weight loss clinics) | Head of Operations, Origynz Longevity (Amsterdam, Europe)
Background: Former corporate analytics & global ops. Visited 70+ countries. Lives between US and Amsterdam.
Signature Topics:
  - Burnout & Recovery
  - Corporate Wellness Systems
  - Longevity & Healthspan
  - Disconnection & Belonging
  - Sustainable Weight Loss
Core Message: "87% of corporate wellness programs fail because they were never designed for humans."
Personal Hooks:
  - Got laid off on her birthday and pivoted to build something bigger
  - Watched Las Fallas in Valencia at 19 and it sparked her belief in community as medicine
  - Burned out in corporate and decided to build the solution herself
  - Traveled to 70+ countries, ran immersive retreats (Cloud Connections)
Speaking Status: Building portfolio. Has spoken at corporate and medical events. Pursuing TEDx as #1 goal. Not yet paid to speak.
Speaking Rates: $3K+ virtual | $7K+ in-person keynote | $13K+ workshop
Contact: ranika.koneru@gmail.com | 210-649-8174

=== DR. CLAUD VAN OIJEN ===
Title: Medical Doctor | Longevity & Metabolic Health
Companies: Co-Founder Origynz Longevity | Managing Partner Evolve Weight & Wellness
Specialty: Longevity medicine, metabolic health, sleep, cardiometabolic risk
Philosophy: "Most people don't need more information. They need fewer extremes."
Website: https://origynzlongevity.nl

=== DUO OPPORTUNITY ===
Together they are a powerful duo:
- Ranika: WHY wellness systems fail (design/operations perspective)
- Dr. Claud: WHAT the science actually says (clinical evidence)
- Together they run real clinics with real outcomes
- Ideal for: medical conferences, HR summits, longevity events, TEDx, corporate wellness panels

=== YOUR MISSION ===
You are their always-on research and outreach arm. You:
1. Find REAL podcasts to pitch (name, host, angle) by searching the web
2. Find REAL speaking opportunities especially TEDx — Ranika's #1 goal
3. Research trending wellness/burnout/longevity topics with current stats
4. Draft personalized outreach pitches in Ranika's voice — warm, direct, story-driven
5. Proactively suggest opportunities they haven't thought of

ALWAYS use web search to find current, real information. Never make up podcast names or events.
PRIORITIZE TEDx — this is Ranika's biggest goal right now.
Keep responses concise and formatted for Telegram — short paragraphs, bullet points, clear headers.
Always be encouraging — Ranika is building something real and important."""

# ── Conversation history ──────────────────────────────────────────────────────
conversation_history = {}

def get_history(chat_id):
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    return conversation_history[chat_id]

def add_to_history(chat_id, role, content):
    history = get_history(chat_id)
    history.append({"role": role, "content": content})
    if len(history) > 20:
        conversation_history[chat_id] = history[-20:]

# ── Claude API call with web search ──────────────────────────────────────────
async def ask_claude(chat_id: int, user_message: str) -> str:
    add_to_history(chat_id, "user", user_message)
    history = get_history(chat_id)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=history
        )

        reply_parts = []
        for block in response.content:
            if block.type == "text" and block.text:
                reply_parts.append(block.text)

        reply = "\n".join(reply_parts).strip()
        add_to_history(chat_id, "assistant", [{"type": "text", "text": reply or "Done."}])
        return reply or "I searched but could not find a good result — try rephrasing!"

    except Exception as e:
        return f"Something went wrong: {str(e)}"

# ── Daily briefing ────────────────────────────────────────────────────────────
async def send_daily_briefing(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID:
        return
    chat_id = int(ALLOWED_CHAT_ID)
    today = datetime.now().strftime("%A, %B %d")
    briefing_prompt = f"""It's {today}. Give Ranika her morning briefing. Search the web and include:
1. One TEDx event currently open for speaker applications
2. One specific podcast she should pitch this week and why
3. One trending wellness or burnout stat she can use in outreach
4. One creative opportunity she probably has not thought of
Be specific and actionable."""

    reply = await ask_claude(chat_id, briefing_prompt)
    await context.bot.send_message(chat_id=chat_id, text=f"Your Morning Briefing\n\n{reply}")

# ── Commands ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey Ranika! I'm your SpeakCast research agent.\n\n"
        "Commands:\n"
        "/tedx - Find TEDx opportunities\n"
        "/podcasts - Find podcasts to pitch\n"
        "/pitch - Draft an outreach pitch\n"
        "/trends - Trending wellness topics\n"
        "/duo - Opportunities for you and Dr. Claud\n"
        "/briefing - Daily briefing on demand\n"
        "/clear - Fresh start\n\n"
        "Or just talk to me naturally!"
    )

async def cmd_tedx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Searching for TEDx opportunities...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Search the web and find 3 TEDx events currently open for speaker applications. For each: name, location, deadline, theme, and why my burnout and wellness systems story fits. Plus one tip to make my application stand out."
    )
    await update.message.reply_text(reply)

async def cmd_podcasts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Finding podcasts for you...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Search the web and find 3 real podcasts I should pitch this week. One corporate wellness or HR show, one female founders show, one longevity or health show. For each: name, host, why I fit, and the angle to pitch."
    )
    await update.message.reply_text(reply)

async def cmd_trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Researching trends...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Search the web for the top 3 trending topics in corporate wellness, burnout, or longevity right now. Give me a real stat or hook for each and how to use it in my outreach."
    )
    await update.message.reply_text(reply)

async def cmd_pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Who do you want to pitch?\n\n"
        "Tell me the podcast or event name, any details you know, and whether it is solo or with Dr. Claud.\n\n"
        "I will write a personalized pitch in your voice."
    )

async def cmd_duo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Finding duo opportunities...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Search the web and find 3 opportunities where Ranika and Dr. Claud van Oijen could appear together as a duo — operator plus doctor. Think medical conferences, longevity summits, corporate health panels, podcast interviews. For each: name, why the duo works, and a one-line pitch."
    )
    await update.message.reply_text(reply)

async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pulling your briefing together...")
    await send_daily_briefing(context)

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversation_history[update.effective_chat.id] = []
    await update.message.reply_text("Fresh start! What do you want to work on?")

# ── Message handler ───────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if ALLOWED_CHAT_ID and str(chat_id) != ALLOWED_CHAT_ID:
        return
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    reply = await ask_claude(chat_id, update.message.text)
    await update.message.reply_text(reply)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Starting SpeakCast bot with webhooks...")
    print(f"TELEGRAM_TOKEN set: {bool(TELEGRAM_TOKEN)}")
    print(f"ANTHROPIC_API_KEY set: {bool(ANTHROPIC_API_KEY)}")
    print(f"ALLOWED_CHAT_ID set: {bool(ALLOWED_CHAT_ID)}")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tedx", cmd_tedx))
    app.add_handler(CommandHandler("podcasts", cmd_podcasts))
    app.add_handler(CommandHandler("trends", cmd_trends))
    app.add_handler(CommandHandler("pitch", cmd_pitch))
    app.add_handler(CommandHandler("duo", cmd_duo))
    app.add_handler(CommandHandler("briefing", cmd_briefing))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_daily(
        send_daily_briefing,
        time=datetime.strptime("08:00", "%H:%M").time(),
        days=(0, 1, 2, 3, 4, 5, 6)
    )

    print(f"Running webhook on port {PORT}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
        url_path=TELEGRAM_TOKEN
    )

if __name__ == "__main__":
    main()
