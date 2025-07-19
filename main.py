import os
import asyncio
import logging
import aiohttp
import pytz
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load from environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Example: -100xxxxxxxxxx
WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")

# Create Pyrogram bot
app = Client("newsbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🔍 Function to fetch top news using World News API
async def fetch_top_news():
    url = f"https://api.worldnewsapi.com/search-news?text=ભારત&number=5&language=gu&api-key={WORLD_NEWS_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data.get("news", [])


# 📰 Send news every 2 minutes to CHANNEL
async def send_news():
    news_items = await fetch_top_news()
    if not news_items:
        logger.warning("No news found.")
        return

    for item in news_items:
        title = item.get("title", "No title")
        description = item.get("text", "No description")
        url = item.get("url", "")
        source = item.get("source", "")

        message = f"📰 <b>{title}</b>\n\n📜 {description}\n\n🔗 Source: <a href='{url}'>{source}</a>"
        await app.send_message(CHANNEL_ID, message, parse_mode="HTML", disable_web_page_preview=True)


# Scheduler (every 2 minutes)
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Kolkata"))
scheduler.add_job(send_news, "interval", minutes=2)

# /start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply("👋 Welcome to the News Bot!\nYou’ll receive top news updates every 2 minutes.")

# /ping command
@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(client, message: Message):
    await message.reply("✅ Bot is alive!")

# /news command to manually fetch news
@app.on_message(filters.command("news") & filters.user(OWNER_ID))
async def manual_news(client, message: Message):
    news_items = await fetch_top_news()
    if not news_items:
        await message.reply("No news found at the moment.")
        return

    text = "🗞️ <b>Top News:</b>\n\n"
    for item in news_items:
        title = item.get("title")
        url = item.get("url")
        source = item.get("source")
        text += f"• <a href='{url}'>{title}</a> ({source})\n"

    await message.reply(text, disable_web_page_preview=True)

# 🔁 Main async runner
async def main():
    await app.start()
    logger.info("🚀 Bot started")
    await app.send_message(OWNER_ID, "✅ News Bot started and running!")
    scheduler.start()
    await idle()
    await app.stop()

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
