import os
import logging
import asyncio
import requests
from typing import List
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables (from Render or .env)
API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "").strip().replace('"', '')
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip().replace('"', '')
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip().replace('"', '')
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", ""))
OWNER_ID = int(os.environ.get("OWNER_ID", ""))

# Optional extras
AUTH_USERS = [OWNER_ID]
BUTTONSCONTACT = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Creator 👑", url="http://t.me/CHOSEN_ONEx_bot")]]
)

# Pyrogram Client
app = Client("newsbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def get_latest_news() -> List[str]:
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    headers = {"User-Agent": "TelegramNewsBot/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])[:5]
        if not articles:
            raise Exception("No articles found in response.")
        return [
            f"📰 <b>{a.get('title')}</b>\n\n{a.get('description')}\n🔗 <a href='{a.get('url')}'>Read More</a>"
            for a in articles
        ]
    except Exception as e:
        logger.error(f"Error fetching news: {e} | URL used: {url}")
        return ["❌ Failed to fetch news."]


async def send_news():
    news_items = get_latest_news()
    for news in news_items:
        try:
            await app.send_message(chat_id=TARGET_CHAT_ID, text=news, parse_mode="html", disable_web_page_preview=False)
            await app.send_message(chat_id=OWNER_ID, text=news, parse_mode="html", disable_web_page_preview=False)
        except Exception as e:
            logger.error(f"Error sending news: {e}")


@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    user = m.from_user
    welcome_text = (
        f"👋 Hello, <b>{user.first_name}</b>!\n\n"
        "📢 This bot sends the latest news updates every 2 minutes.\n"
        "📰 Stay updated with top headlines from India!\n\n"
        "✅ You will receive the news directly in your PM or a channel.\n\n"
        "✨ Powered by <b>NewsAPI</b> & Pyrogram."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 Contact Owner", url="https://t.me/CHOSEN_ONEx_bot")],
        [InlineKeyboardButton("🌐 Visit NewsAPI", url="https://newsapi.org/")]
    ])
    await m.reply_text(welcome_text, reply_markup=buttons, parse_mode="html")


# Schedule the news sending job
scheduler = AsyncIOScheduler()
scheduler.add_job(send_news, "interval", minutes=2)
scheduler.start()

# Notify on startup
@app.on_message(filters.command("restart") & filters.user(AUTH_USERS))
async def restart_msg(_, m: Message):
    await m.reply("🔄 Bot Restarted and Scheduler is Running!")

# Start the bot
if __name__ == "__main__":
    logger.info("🤖 Bot started. Scheduler initialized.")
    app.run()
