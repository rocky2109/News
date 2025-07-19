import os
import asyncio
import pytz
import logging
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging
logging.basicConfig(level=logging.INFO)

# ENV Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))  # Your Telegram user ID
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Add this to Koyeb env
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")  # @yourchannelusername or channel ID

# India timezone
india = pytz.timezone("Asia/Kolkata")

# Bot client
app = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Fetch news
async def fetch_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data["status"] != "ok":
                    logging.warning("News API returned error.")
                    return None
                articles = data["articles"][:5]
                news_text = "\n\n".join([f"📰 <b>{a['title']}</b>\n<a href='{a['url']}'>Read more</a>" for a in articles])
                return f"<b>🗞️ Top Headlines (India):</b>\n\n{news_text}"
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return None

# Send news every 2 mins
async def send_news():
    news = await fetch_news()
    if news:
        try:
            await app.send_message(TARGET_CHANNEL, news, disable_web_page_preview=True)
            logging.info("✅ News sent to channel.")
        except Exception as e:
            logging.error(f"Failed to send news: {e}")

# Start command
@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    await m.reply_text("👋 Hello! I am your automated Indian news bot.\n\nI will send top headlines to the configured channel every 2 minutes.")

# Notify owner
async def notify_owner():
    try:
        await app.send_message(OWNER_ID, "✅ Bot has started successfully and is fetching news every 2 minutes.")
    except Exception as e:
        logging.warning(f"Could not send message to owner: {e}")

# Run app
async def main():
    await app.start()
    await notify_owner()

    scheduler = AsyncIOScheduler(timezone=india)
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()

    print("✅ Bot is running...")
    await idle()
    await app.stop()

# Needed for idle() import
from pyrogram.idle import idle

if __name__ == "__main__":
    asyncio.run(main())
