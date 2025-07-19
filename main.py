import os
import asyncio
import logging
import aiohttp
import pytz
from datetime import datetime
from pyrogram import Client, filters, idle, enums
from pyrogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ✅ Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Load from environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Example: -100xxxxxxxxxx
WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")

# ✅ Create Pyrogram client
app = Client("newsbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🔍 Fetch Gujarati news using World News API
async def fetch_top_news():
    url = f"https://api.worldnewsapi.com/search-news?text=ભારત&number=5&language=gu&api-key={WORLD_NEWS_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to fetch news. Status code: {resp.status}")
                    return []
                data = await resp.json()
                return data.get("news", [])
    except Exception as e:
        logger.exception(f"Error fetching news: {e}")
        return []

# 📢 Send news to channel
import json
import random
from pyrogram import enums

SENT_NEWS_FILE = "sent_news.json"
EMOJIS = ["📰", "📢", "🗞️", "🧠", "📜", "🌐", "🔔", "✅", "📍", "🕘"]

# Load previously sent URLs
def load_sent_news():
    try:
        with open(SENT_NEWS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

# Save sent URLs
def save_sent_news(sent_set):
    with open(SENT_NEWS_FILE, "w") as f:
        json.dump(list(sent_set), f)


async def send_news():
    sent_news = load_sent_news()
    news_items = await fetch_top_news()
    if not news_items:
        logger.warning("No news found.")
        return

    count = 0
    for item in news_items:
        url = item.get("url", "")
        if url in sent_news:
            continue  # Skip duplicates

        title = item.get("title", "No title").strip()
        description = item.get("text", "No description").strip()
        source = item.get("source", "")

        emoji = random.choice(EMOJIS)
        message = f"{emoji} <b>{title}</b>\n\n📜 {description}\n\n🔗 <a href='{url}'>{source}</a>"

        # Trim if too long
        if len(message) > 4096:
            max_len = 4096 - len(f"{emoji} <b>{title}</b>\n\n📜 \n\n🔗 <a href='{url}'>{source}</a>") - 10
            description = description[:max_len] + "..."
            message = f"{emoji} <b>{title}</b>\n\n📜 {description}\n\n🔗 <a href='{url}'>{source}</a>"

        try:
            await app.send_message(CHANNEL_ID, message, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            sent_news.add(url)
            count += 1
        except Exception as e:
            logger.error(f"❌ Failed to send: {e}")

        if count >= 5:
            break  # Send only top 5 highlights

    save_sent_news(sent_news)



scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Kolkata"))

# 🔁 Every 3 hours (00:00, 03:00, 06:00, ..., 21:00 IST)
scheduler.add_job(send_news, "interval", minutes=2)

# 🕗 Daily at 8:00 PM IST
scheduler.add_job(send_news, "cron", hour=20, minute=0)

scheduler.start()

# 👋 /start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply("👋 Welcome to the News Bot!\n\n📢 You’ll receive Gujarati current affairs every 2 minutes!")

# 💓 /ping command
@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(client, message: Message):
    await message.reply("✅ Bot is alive!")

# 🗞️ /news command to manually fetch and send top news
@app.on_message(filters.command("news") & filters.user(OWNER_ID))
async def manual_news(client, message: Message):
    news_items = await fetch_top_news()
    if not news_items:
        await message.reply("😕 No news found at the moment.")
        return

    text = "🗞️ <b>Gujarati Top News:</b>\n\n"
    for item in news_items:
        title = item.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
        url = item.get("url", "")
        source = item.get("source", "Source")
        text += f"• <a href='{url}'>{title}</a> ({source})\n"

    await message.reply(text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

# 🚀 Main runner
async def main():
    await app.start()
    logger.info("✅ News Bot started")
    await app.send_message(OWNER_ID, "🚀 News Bot started successfully!")
    scheduler.start()
    await idle()
    await app.stop()
    logger.info("🛑 Bot stopped")

# 🔁 Run
if __name__ == "__main__":
    asyncio.run(main())
