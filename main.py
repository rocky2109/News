import os
import asyncio
import logging
import requests
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Env variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Timezone
INDIAN_TZ = timezone("Asia/Kolkata")

# Pyrogram bot client
app = Client("NewsBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to fetch latest news
def fetch_latest_news():
    try:
        res = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}")
        data = res.json()
        if data["status"] == "ok" and data["articles"]:
            article = data["articles"][0]
            title = article.get("title", "No Title")
            description = article.get("description", "")
            url = article.get("url", "")
            return f"📰 {title}\n\n{description}\n\nLink: {url}"
        return None
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return None

# News sending job
async def send_news():
    news = fetch_latest_news()
    if news:
        try:
            await app.send_message(CHANNEL_ID, news, disable_web_page_preview=True)
            await app.send_message(OWNER_ID, f"News sent:\n\n{news}", disable_web_page_preview=True)
        except Exception as e:
            await app.send_message(OWNER_ID, f"Failed to send news:\n{e}")
    else:
        await app.send_message(OWNER_ID, "No news fetched.")

# /start command
@app.on_message(filters.command("start") & filters.private)
async def start_handler(_, message: Message):
    await message.reply(
        "Hello!\nI'm your automated Indian News Bot.\nI’ll keep you updated with top headlines every 2 minutes!"
    )

# Run bot
async def main():
    await app.start()
    await app.send_message(OWNER_ID, "Bot started and news scheduler is active!")

    # Scheduler in event loop
    scheduler = AsyncIOScheduler(timezone=INDIAN_TZ)
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
