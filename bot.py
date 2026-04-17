import os
import asyncio
import anthropic
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx

# ── Config ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ALLOWED_CHAT_ID = os.environ.get("ALLOWED_CHAT_ID")  # your personal Telegram chat ID

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
Core Message: "87% of corporate wellness programs fail — not because people lack motivation, but because the systems were never designed for humans."
Personal Hooks:
  - Got laid off on her birthday → pivoted and built something bigger
  - Watched Las Fallas in Valencia at 19 → sparked lifelong belief in community as medicine
  - Burned out in corporate → decided to build the solution herself
  - Traveled to 70+ countries, ran immersive retreats (Cloud Connections)
Speaking Status: Building her portfolio. Has spoken at corporate and medical events. Pursuing TEDx as her next major goal. Not yet paid to speak — seeking both free stages to build reel AND paid opportunities.
Speaking Rates (when paid): $3K+ virtual keynote | $7K+ in-person keynote | $13K+ in-person workshop
Contact: ranika.koneru@gmail.com | linkedin.com/in/ranikakoneru | 210-649-8174
Testimonials: "Transformational" (medical doctor), "Powerhouse speaker" (business owner), "Must-book" (global connector)

=== DR. CLAUD VAN OIJEN ===
Title: Medical Doctor | Longevity & Metabolic Health
Companies: Co-Founder, Origynz Longevity | Managing Partner, Evolve Weight & Wellness
Specialty: Longevity medicine, metabolic health, sleep, cardiometabolic risk, aging mechanisms
Philosophy: "Most people don't need more information. They need fewer extremes." Focuses on sustainable adherence, not optimization theater.
Key Message: Longevity stops being theoretical when people can actually live with it. He translates complex medical concepts into decisions people can sustain.
Location: Netherlands (building Origynz in Europe) + US consulting
Website: https://origynzlongevity.nl

=== DUO OPPORTUNITY ===
Together, Ranika (systems operator) + Dr. Claud (clinical doctor) are a rare and compelling duo:
- She speaks to WHY wellness systems fail (design problem)
- He speaks to WHAT the science actually says (evidence without extremes)
- Together they run real clinics with real patient outcomes
- This combo is ideal for: medical conferences, HR summits, longevity events, corporate wellness panels, TEDx events

=== YOUR MISSION ===
You are their always-on research arm. Your job:
1. Find REAL podcast opportunities (give show name, host, why it fits, pitch angle)
2. Find REAL speaking opportunities (TEDx events, conferences, summits — especially ones actively seeking speakers)
3. Research trending wellness/longevity/burnout topics they should be speaking on
4. Draft personalized outreach pitches in Ranika's voice — warm, direct, story-driven, not templated
5. Proactively suggest ideas they haven't thought of

ALWAYS search the web for current, real information. Never make up podcast names or events.
PRIORITIZE TEDx opportunities — this is Ranika's #1 goal right now.
Be specific. Be actionable. Treat every message like it matters to their career.
Keep responses concise for Telegram — use short paragraphs, bullet points, and clear headers.
"""

# ── Conversation history per chat ─────────────────────────────────────────────
conversation_history = {}

def get_history(chat_id):
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    return conversation_history[chat_id]

def add_to_history(chat_id, role, content):
    history = get_history(chat_id)
    history.append({"role": role, "content": content})
    # Keep last 20 exchanges to avoid token limits
    if len(history) > 40:
        conversation_history[chat_id] = history[-40:]

# ── Claude API call with web search ──────────────────────────────────────────
async def ask_claude(chat_id: int, user_message: str) -> str:
    add_to_history(chat_id, "user", user_message)
    history = get_history(chat_id)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=history
        )

        # Extract text from response
        reply = ""
        for block in response.content:
            if block.type == "text":
                reply += block.text

        add_to_history(chat_id, "assistant", response.content)
        return reply.strip() or "I couldn't find anything on that — try rephrasing?"

    except Exception as e:
        return f"Something went wrong: {str(e)}"

# ── Daily briefing ────────────────────────────────────────────────────────────
async def send_daily_briefing(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID:
        return
    chat_id = int(ALLOWED_CHAT_ID)
    today = datetime.now().strftime("%A, %B %d")
    briefing_prompt = f"""Good morning Ranika! It's {today}. 

Give me today's proactive briefing. Search the web and include:
1. 🎤 One TEDx event currently open for speaker applications
2. 🎙️ One podcast that would be perfect for me to pitch this week
3. 📊 One trending wellness/burnout/longevity stat or story I can use in outreach or social
4. 💡 One outreach idea or opportunity I probably haven't thought of

Keep it tight and actionable. I want to be able to act on at least one of these today."""

    reply = await ask_claude(chat_id, briefing_prompt)
    await context.bot.send_message(chat_id=chat_id, text=f"☀️ *Your Morning Briefing*\n\n{reply}", parse_mode="Markdown")

# ── Command handlers ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey Ranika! I'm your SpeakCast research agent.\n\n"
        "I'm here to help you land that TEDx stage, find podcasts, draft pitches, and stay ahead of wellness trends.\n\n"
        "Just talk to me naturally or use these commands:\n\n"
        "/tedx — Find open TEDx opportunities\n"
        "/podcasts — Find podcasts to pitch\n"
        "/pitch — Draft an outreach pitch\n"
        "/trends — What's trending in wellness right now\n"
        "/duo — Find joint opportunities for you + Dr. Claud\n"
        "/briefing — Get your daily research briefing\n"
        "/clear — Start a fresh conversation"
    )

async def cmd_tedx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Searching for open TEDx opportunities...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Find me 3 TEDx events that are currently open for speaker applications or will be opening soon. For each one give me: event name, location, application deadline if known, their theme, and why my story about burnout/wellness systems/belonging would be a strong fit. Search for real current listings."
    )
    await update.message.reply_text(reply)

async def cmd_podcasts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎙️ Finding the right podcasts for you...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Find me 3 real podcasts I should pitch this week. Mix of: corporate wellness/HR, female founder/entrepreneur, and longevity/health. For each: show name, host, approximate audience size, why I'm a fit, and the specific angle I should pitch. Look for shows that actively feature guests."
    )
    await update.message.reply_text(reply)

async def cmd_trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Researching what's trending...")
    reply = await ask_claude(
        update.effective_chat.id,
        "What are the top 3 trending topics right now in corporate wellness, burnout, or longevity that I should be speaking on and referencing in outreach? Give me real stats, recent studies, or news hooks I can use. Make each one actionable — how do I weave it into my pitch or talk?"
    )
    await update.message.reply_text(reply)

async def cmd_pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✍️ Who do you want to pitch? Just tell me:\n\n"
        "- The podcast or event name\n"
        "- Any details you know about them\n"
        "- Whether it's for you solo or you + Dr. Claud\n\n"
        "I'll write a personalized pitch in your voice."
    )

async def cmd_duo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Finding duo opportunities for you and Dr. Claud...")
    reply = await ask_claude(
        update.effective_chat.id,
        "Find 3 opportunities where Ranika (wellness systems operator) and Dr. Claud (longevity medical doctor) could speak or appear TOGETHER as a duo. Think: medical conferences, longevity summits, corporate health events, podcast duos, panel discussions. For each: name the opportunity, explain why the duo format is powerful here, and give a one-line pitch angle for them together."
    )
    await update.message.reply_text(reply)

async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("☀️ Pulling your briefing together...")
    await send_daily_briefing(context)

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conversation_history[chat_id] = []
    await update.message.reply_text("🧹 Fresh start! What do you want to work on?")

# ── Main message handler ──────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Security: only respond to allowed user
    if ALLOWED_CHAT_ID and str(chat_id) != ALLOWED_CHAT_ID:
        return

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    reply = await ask_claude(chat_id, user_text)
    await update.message.reply_text(reply)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tedx", cmd_tedx))
    app.add_handler(CommandHandler("podcasts", cmd_podcasts))
    app.add_handler(CommandHandler("trends", cmd_trends))
    app.add_handler(CommandHandler("pitch", cmd_pitch))
    app.add_handler(CommandHandler("duo", cmd_duo))
    app.add_handler(CommandHandler("briefing", cmd_briefing))
    app.add_handler(CommandHandler("clear", cmd_clear))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Daily briefing at 8am UTC (adjust to your timezone)
    app.job_queue.run_daily(
        send_daily_briefing,
        time=datetime.strptime("08:00", "%H:%M").time(),
        days=(0, 1, 2, 3, 4, 5, 6)
    )

    print("SpeakCast bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
