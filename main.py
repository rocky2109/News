import os
import asyncio
import logging
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load from environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = os.getenv("CHANNEL_ID")  # e.g., -100xxxxxxxxxx
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Create Pyrogram bot
app = Client("newsbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to fetch news
def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=in&pageSize=5&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return "Failed to fetch news."

    data = response.json()
    articles = data.get("articles")

    if not articles:
        return "No news found at the moment."

    news_texts = []
    for article in articles:
        title = article.get("title", "No Title")
        url = article.get("url", "")
        news_texts.append(f"{title}\n{url}")

    return "\n\n".join(news_texts)

# Send news every 2 minutes
async def send_news():
    news = fetch_top_news()
    try:
        await app.send_message(chat_id=int(CHANNEL_ID), text=news)
        await app.send_message(chat_id=int(OWNER_ID), text=f"✅ News sent:\n\n{news}")
    except Exception as e:
        logger.error(f"Error sending news: {e}")

# Start scheduler
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Kolkata"))
scheduler.add_job(send_news, "interval", minutes=2)

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply("👋 Welcome to the News Bot!\nYou’ll receive top news updates every 2 minutes.")

# Notify owner on bot start
@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(client, message: Message):
    await message.reply("✅ Bot is alive!")

@app.on_message(filters.command("news") & filters.user(OWNER_ID))
async def manual_news(client, message: Message):
    news = fetch_top_news()
    await message.reply(news)

# Main
async def main():
    await app.start()
    logger.info("🚀 Bot started")
    await app.send_message(OWNER_ID, "✅ News Bot started and running!")
    scheduler.start()
    await idle()
    await app.stop()

from pyrogram import idle

if __name__ == "__main__":
    asyncio.run(main())
