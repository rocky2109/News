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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY")

# Constants
EMOJIS = ["📰", "📢", "🗞️", "🧠", "📜", "🌐", "🔔", "✅", "📍", "🕘"]
HEADERS = ["🧠 Quick Highlights", "🔥 Top News", "📌 Daily Brief"]
SENT_NEWS_FILE = "sent_news.json"
TIMEZONE = pytz.timezone("Asia/Kolkata")

# Initialize Pyrogram client
app = Client("news-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# News cache manager
class NewsCache:
    def __init__(self):
        self.sent_urls = set()
        self.load()
    
    def load(self):
        try:
            with open(SENT_NEWS_FILE, "r") as f:
                self.sent_urls = set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            self.sent_urls = set()
    
    def save(self):
        with open(SENT_NEWS_FILE, "w") as f:
            json.dump(list(self.sent_urls), f)
    
    def add(self, url):
        self.sent_urls.add(url)
        self.save()

news_cache = NewsCache()

async def fetch_top_english_news():
    """Fetch news from World News API"""
    url = "https://api.worldnewsapi.com/search-news"
    params = {
        "text": "India OR Gujarat",
        "language": "en",
        "number": 10,
        "sort": "published_desc",
        "api-key": WORLD_NEWS_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    logger.error(f"API Error: Status {resp.status}")
                    return []
                return await resp.json()
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return []

def format_news_item(item):
    """Format a single news item for Telegram"""
    title = item.get("title", "").strip()
    url = item.get("url", "").strip()
    source = item.get("source", {}).get("name", "Unknown")
    
    if not title or not url or url in news_cache.sent_urls:
        return None
        
    return f"{random.choice(EMOJIS)} <a href='{url}'>{title[:80]}</a> ({source})"

async def send_news():
    """Send news update every 2 minutes"""
    try:
        # Fetch news
        news_data = await fetch_top_english_news()
        news_items = news_data.get("news", [])
        
        if not news_items:
            logger.warning("No news items available")
            return

        # Process news
        new_items = []
        for item in news_items:
            formatted = format_news_item(item)
            if formatted:
                new_items.append(formatted)
                news_cache.add(item["url"])

        if not new_items:
            logger.info("No new items after filtering")
            return

        # Prepare message
        message = (
            f"<b>{random.choice(HEADERS)}</b>\n\n" +
            "\n".join(new_items[:5]) +  # Limit to 5 items
            f"\n\n⏰ {datetime.now(TIMEZONE).strftime('%d %b %Y, %I:%M %p')}"
        )

        # Send message
        await app.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info("News update sent successfully")

    except Exception as e:
        logger.error(f"Error in send_news: {e}")

scheduler = AsyncIOScheduler(timezone=TIMEZONE)
scheduler.add_job(send_news, "interval", minutes=2)

# Bot commands
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply("✅ News bot is running!")

# Scheduler setup


async def main():
    await app.start()
    logger.info("Bot started")
    await app.send_message(OWNER_ID, "🚀 News bot is now running!")
    
    scheduler.start()
    logger.info("Scheduler started (2-minute intervals)")
    
    await idle()
    
    scheduler.shutdown()
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
