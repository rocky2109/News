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
WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")

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
async def fetch_top_news():
    url = "https://api.worldnewsapi.com/search-news"
    params = {
        "text": "ભારત",
        "language": "gu",
        "number": 10,
        "sort": "published_desc"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    error = await resp.json()
                    logger.error(f"Fetch error {resp.status}: {error.get('message')}")
                    return []
                data = await resp.json()
                return data.get("news", [])
    except Exception as e:
        logger.exception(f"Exception in fetch_top_news: {e}")
        return []


# ✅ Send top Gujarati news
async def send_news():
    sent_urls = load_sent_news()
    news_items = await fetch_top_news()

    if not news_items:
        logger.warning("No news to send.")
        return

    count = 0
    for item in news_items:
        url = item.get("url")
        if url in sent_urls:
            continue  # Skip duplicates

        title = item.get("title", "No title").strip()
        desc = item.get("text", "No description").strip()
        source = item.get("source", "🌐 Source")

        emoji = random.choice(EMOJIS)
        message = f"{emoji} <b>{title}</b>\n\n📜 {desc}\n\n🔗 <a href='{url}'>{source}</a>"

        # Trim if too long
        if len(message) > 4096:
            max_len = 4096 - len(f"{emoji} <b>{title}</b>\n\n📜 \n\n🔗 <a href='{url}'>{source}</a>") - 10
            desc = desc[:max_len] + "..."
            message = f"{emoji} <b>{title}</b>\n\n📜 {desc}\n\n🔗 <a href='{url}'>{source}</a>"

        try:
            await app.send_message(CHANNEL_ID, message, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            sent_urls.add(url)
            count += 1
        except Exception as e:
            logger.error(f"Send error: {e}")

        if count >= 5:
            break  # Limit to 5 news per job

    save_sent_news(sent_urls)

# ✅ Scheduler setup
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Kolkata"))
scheduler.add_job(send_news, "cron", hour=20, minute=0)  # Every day at 8 PM
scheduler.add_job(send_news, "interval", minutes=2)        # Every 3 hours

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
