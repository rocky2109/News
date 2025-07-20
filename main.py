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
    
# In your NewsCache class, modify the add() method:
    def add(self, url):
    # Keep only the 100 most recent URLs to prevent over-filtering
        if len(self.sent_urls) >= 100:
            self.sent_urls = set(list(self.sent_urls)[-100:])
        self.sent_urls.add(url)
        self.save()

news_cache = NewsCache()

async def fetch_top_english_news():
    """Fetch news from World News API with proper error handling"""
    url = "https://api.worldnewsapi.com/search-news"
    params = {
        "text": "India OR Gujarat",
        "language": "en",
        "number": 10,
        "sort": "publish-time",  # Changed from 'published_desc' to 'publish-time'
        "api-key": WORLD_NEWS_API_KEY,
        "earliest-publish-date": datetime.now(TIMEZONE).strftime("%Y-%m-%d")  # Get only today's news
    
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"API Error {resp.status}: {error_text}")
                    return []
                
                data = await resp.json()
                if data.get("status") == "failure":
                    logger.error(f"API Failure: {data.get('message')}")
                    return []
                return data.get("news", [])
                
    except asyncio.TimeoutError:
        logger.warning("News API request timed out")
        return []
    except Exception as e:
        logger.error(f"News fetch error: {e}", exc_info=True)
        return []

def format_news_item(item):
    """Format a single news item with validation"""
    if not isinstance(item, dict):
        return None
        
    title = item.get("title", "").strip()
    url = item.get("url", "").strip()
    source = item.get("source", {}).get("name", "Unknown") if isinstance(item.get("source"), dict) else "Unknown"
    
    if not title or not url or url in news_cache.sent_urls:
        return None
        
    return f"{random.choice(EMOJIS)} <a href='{url}'>{title[:80]}</a> ({source})"

async def send_news():
    """Send news update with enhanced error handling"""
    try:
        logger.info("Starting news fetch...")
        news_items = await fetch_top_english_news()
        
        if not news_items:
            logger.warning("No news items available")
            return

        new_items = []
        for item in news_items:
            formatted = format_news_item(item)
            if formatted:
                new_items.append(formatted)
                news_cache.add(item["url"])

        if not new_items:
            logger.info("No new items after filtering")
            return

        message = (
            f"<b>{random.choice(HEADERS)}</b>\n\n" +
            "\n".join(new_items) +
            f"\n\n⏰ {datetime.now(TIMEZONE).strftime('%d %b %Y, %I:%M %p')}"
        )

        await app.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info("News update sent successfully")

    except Exception as e:
        logger.error(f"Error in send_news: {e}", exc_info=True)

# Command handlers
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    try:
        await message.reply_text(
            "📰 Welcome to News Bot!\n\n"
            "I'll send you news updates regularly.\n"
            "Commands:\n"
            "/start - Show this message\n"
            "/news - Get latest news\n"
            "/ping - Check bot status",
            parse_mode=enums.ParseMode.HTML
        )
        logger.info(f"Responded to start command from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
scheduler.add_job(send_news, "interval", minutes=2)

# Replace your run_bot() function with:
async def main():
    await app.start()
    logger.info("Bot started")
    await app.send_message(OWNER_ID, "✅ Bot is running with scheduler.")
    
    # Start scheduler
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()
    logger.info("Scheduler started")
    
    # Create a permanent task to keep the bot running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown()
        await app.stop()
        logger.info("Bot stopped")

if __name__ == "__main__":
    # Configure asyncio to use uvloop if available (faster)
    try:
        import uvloop
        uvloop.install()
        logger.info("Using uvloop for better performance")
    except ImportError:
        pass
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        loop.close()
        logger.info("Event loop closed")
