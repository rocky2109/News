import os
import asyncio
import logging
import aiohttp
import pytz
import json
import random
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters, enums, idle
from pyrogram.types import Message

# ✅ Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WORLD_NEWS_API_KEY = os.getenv("e5cc1447cb6548eb8edb4771bc145fd2")

# ✅ Pyrogram Client
app = Client("gujarati-news-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ✅ Emojis and sent news record file
EMOJIS = ["📰", "📢", "🗞️", "🧠", "📜", "🌐", "🔔", "✅", "📍", "🕘"]
SENT_NEWS_FILE = "sent_news.json"

# ✅ Load previously sent news URLs
def load_sent_news():
    try:
        with open(SENT_NEWS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

# ✅ Save sent news URLs
def save_sent_news(sent_urls):
    with open(SENT_NEWS_FILE, "w") as f:
        json.dump(list(sent_urls), f)

# ✅ Fetch Gujarati news using World News API
import random
import aiohttp
import logging

logger = logging.getLogger(__name__)

import os
import random
import aiohttp
import logging
from pyrogram import enums

logger = logging.getLogger(__name__)

# Languages to pick from
LANGUAGES = ["en", "hi", "gu"]
# Emojis for headlines
EMOJIS = ["📰", "🗞️", "📢", "🌍", "⚡", "🔔", "📣", "🚨"]

# HEADERS NOT REQUIRED for this API — uses query param only
async def fetch_top_news():
    selected_language = random.choice(LANGUAGES)
    logger.info(f"🌐 Fetching news in language: {selected_language.upper()}")

    query_text = {
        "en": "India",
        "hi": "भारत",
        "gu": "ભારત"
    }.get(selected_language, "India")

    url = "https://api.worldnewsapi.com/search-news"
    params = {
        "text": query_text,
        "language": selected_language,
        "number": 5,
        "sort": "published_desc",
        "api-key": WORLD_NEWS_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"❌ Failed to fetch news. Status code: {resp.status}")
                    return []
                data = await resp.json()
                return data.get("news", [])
    except Exception as e:
        logger.exception("⚠️ Exception during news fetch:")
        return []

async def send_news():
    news_items = await fetch_top_news()
    if not news_items:
        logger.warning("No news found.")
        return

    highlights = []
    for item in news_items[:5]:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        if title:
            emoji = random.choice(EMOJIS)
            highlights.append(f"{emoji} <a href='{url}'>{title[:80]}</a>")

    if not highlights:
        logger.warning("No valid headlines.")
        return

    header = random.choice(["🧠 Quick Highlights", "🔥 Top News", "📌 Daily Brief"])
    message = f"<b>{header}</b>\n\n" + "\n".join(highlights)

    # Ensure message is under Telegram's limit
    if len(message) > 2000:
        message = message[:1990] + "..."

    try:
        await app.send_message(
            CHANNEL_ID,
            message,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"❌ Failed to send news: {e}")

# ✅ /start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text("👋 Welcome to Gujarati News Bot!\n\n🗞️ Get daily Gujarati current affairs every 3 hours and at 8 PM!\nUse /news to fetch latest manually.")

# ✅ /ping for status
@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping_command(client, message: Message):
    await message.reply_text("✅ Bot is alive and running!")

# ✅ /news to manually send top news
@app.on_message(filters.command("news") & filters.user(OWNER_ID))
async def manual_news_command(client, message: Message):
    news_items = await fetch_top_news()
    if not news_items:
        await message.reply_text("😔 No news available.")
        return

    text = "🗞️ <b>Gujarati Highlights:</b>\n\n"
    for item in news_items[:5]:
        title = item.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
        url = item.get("url", "")
        source = item.get("source", "Source")
        text += f"• <a href='{url}'>{title}</a> ({source})\n"

    await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

# ✅ Bot runner
async def main():
    await app.start()
    logger.info("✅ News Bot started.")
    await app.send_message(OWNER_ID, "🚀 Gujarati News Bot is live!")
    scheduler.start()
    await idle()
    await app.stop()
    logger.info("🛑 Bot stopped.")

# 🔁 Main
if __name__ == "__main__":
    asyncio.run(main())
