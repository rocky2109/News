import asyncio
import logging
import requests
from typing import List
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import API_ID, API_HASH, BOT_TOKEN, NEWS_API_KEY, TARGET_CHAT_ID
from commands import register_commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize bot and scheduler
bot = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

# Fetch latest news articles
def get_latest_news() -> List[str]:
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    headers = {
        "User-Agent": "TelegramNewsBot/1.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        articles = response.json().get("articles", [])[:5]
        news_messages = []

        for article in articles:
            title = article.get("title", "No Title")
            description = article.get("description", "No description available.")
            article_url = article.get("url", "#")

            message = (
                f"📰 <b>{title}</b>\n\n"
                f"{description}\n"
                f"🔗 <a href='{article_url}'>Read More</a>"
            )
            news_messages.append(message)

        return news_messages

    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return ["❌ Failed to fetch news."]

# Send news to the configured chat
async def send_news():
    logging.info("Sending news...")
    for msg in get_latest_news():
        try:
            await bot.send_message(
                TARGET_CHAT_ID,
                msg,
                disable_web_page_preview=False,
                parse_mode="html"
            )
        except Exception as e:
            logging.error(f"Error sending message: {e}")

# Idle loop to keep bot running
async def idle():
    while True:
        await asyncio.sleep(3600)

# Main function to start bot
async def start_bot():
    await bot.start()
    register_commands(bot)
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()
    logging.info("Bot started and scheduler is running.")
    await idle()

import asyncio
from pyrogram import Client
from pyrogram.errors import RPCError

OWNER_ID = int(os.environ.get("OWNER_ID", 6947378236))  # Replace default or load from env

async def notify_owner():
    try:
        await app.send_message(chat_id=OWNER_ID, text="✅ Bot restarted and is now running.")
    except RPCError as e:
        print(f"Failed to notify owner: {e}")

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def main():
    await app.start()
    await notify_owner()
    print("Bot is up and running.")
    await idle()

if __name__ == "__main__":
    import asyncio
    from pyrogram.idle import idle
    asyncio.run(main())
