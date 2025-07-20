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

# ✅ Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Environment variables with validation
try:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID"))
    CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
    WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY") or "5c5e08a86cd44a7381524fdbc469186f"
    
    if not all([API_ID, API_HASH, BOT_TOKEN, OWNER_ID, CHANNEL_ID, WORLD_NEWS_API_KEY]):
        raise ValueError("Missing required environment variables")
except Exception as e:
    logger.error(f"Configuration error: {e}")
    exit(1)

# ✅ Pyrogram Client with better error handling
app = Client(
    "gujarati-news-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Constants
EMOJIS = ["📰", "📢", "🗞️", "🧠", "📜", "🌐", "🔔", "✅", "📍", "🕘"]
HEADERS = ["🧠 Quick Highlights", "🔥 Top News", "📌 Daily Brief"]
SENT_NEWS_FILE = "sent_news.json"
TIMEZONE = pytz.timezone("Asia/Kolkata")

# ✅ News cache management
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

# ✅ Enhanced news fetcher with error handling
async def fetch_top_english_news():
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
                    logger.error(f"News API error: {resp.status}")
                    return []
                
                data = await resp.json()
                return data.get("news", [])
                
    except asyncio.TimeoutError:
        logger.warning("News API request timed out")
        return []
    except Exception as e:
        logger.error(f"News fetch error: {e}", exc_info=True)
        return []

# ✅ News formatter with duplicate prevention
def format_news_item(item):
    title = item.get("title", "").strip()
    url = item.get("url", "").strip()
    source = item.get("source", {}).get("name", "Unknown")
    
    if not title or not url:
        return None
        
    if url in news_cache.sent_urls:
        return None
        
    emoji = random.choice(EMOJIS)
    return f"{emoji} <a href='{url}'>{title[:80]}</a> ({source})"

# ✅ News sender with proper formatting
async def send_news():
    try:
        news_items = await fetch_top_english_news()
        if not news_items:
            logger.warning("No news items received")
            return

        # Process and filter news
        formatted_items = []
        for item in news_items:
            formatted = format_news_item(item)
            if formatted:
                formatted_items.append(formatted)
                news_cache.add(item["url"])
                
        if not formatted_items:
            logger.info("No new news items to send")
            return

        # Prepare message
        message = (
            f"<b>{random.choice(HEADERS)}</b>\n\n" +
            "\n".join(formatted_items[:5]) +  # Limit to 5 items
            f"\n\n⏰ {datetime.now(TIMEZONE).strftime('%d %b %Y, %I:%M %p')}"
        )

        # Send message
        await app.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info("News sent successfully")
        
    except Exception as e:
        logger.error(f"Error in send_news: {e}", exc_info=True)

# ✅ Bot commands
@app.on_message(filters.command("start") & filters.private)
async def start_command(_, message: Message):
    await message.reply_text(
        "👋 Welcome to Gujarati News Bot!\n\n"
        "🗞️ Get daily news updates automatically every 2 hours.\n"
        "Use /news to get the latest updates manually."
    )

@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping_command(_, message: Message):
    await message.reply_text("✅ Bot is running smoothly!")

@app.on_message(filters.command("news") & filters.user(OWNER_ID))
async def manual_news_command(_, message: Message):
    await message.reply_text("⏳ Fetching latest news...")
    await send_news()

# ✅ Bot lifecycle management
async def run_bot():
    await app.start()
    logger.info("Bot started successfully")
    await app.send_message(OWNER_ID, "🚀 Gujarati News Bot is now online!")
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(send_news, "interval", hours=2)
    scheduler.start()
    
    # Keep the bot running
    await idle()
    
    # Cleanup
    scheduler.shutdown()
    await app.stop()
    logger.info("Bot stopped gracefully")

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
