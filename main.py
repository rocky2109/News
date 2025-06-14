import asyncio
import logging
import requests
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import API_ID, API_HASH, BOT_TOKEN, NEWS_API_KEY, TARGET_CHAT_ID

# ✅ Import command handlers
import commands

logging.basicConfig(level=logging.INFO)
bot = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

def get_latest_news():
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        articles = response.json().get("articles", [])[:5]
        news_messages = []

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            message = f"📰 **{title}**\n{description}\n🔗 [Read More]({url})"
            news_messages.append(message)

        return news_messages
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return ["❌ Failed to fetch news."]

async def send_news():
    logging.info("Sending news...")
    news = get_latest_news()
    for msg in news:
        try:
            await bot.send_message(TARGET_CHAT_ID, msg, disable_web_page_preview=False)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

async def start_bot():
    await bot.start()
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()
    logging.info("Bot started and scheduler running.")
    await idle()

async def idle():
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(start_bot())
