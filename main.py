import asyncio
import logging
import requests
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import API_ID, API_HASH, BOT_TOKEN, NEWS_API_KEY, TARGET_CHAT_ID
from commands import register_commands

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize bot
bot = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

# Function to get latest news
def get_latest_news():
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        articles = response.json().get("articles", [])[:5]
        news_messages = []

        for article in articles:
            title = article.get("title", "No Title")
            description = article.get("description", "")
            url = article.get("url", "")
            message = f"📰 **{title}**\n{description}\n🔗 [Read More]({url})"
            news_messages.append(message)

        return news_messages
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return ["❌ Failed to fetch news."]

# Function to send news to Telegram
async def send_news():
    logging.info("Sending news...")
    news = get_latest_news()
    for msg in news:
        try:
            await bot.send_message(TARGET_CHAT_ID, msg, disable_web_page_preview=False)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

# Function to keep the bot alive
async def idle():
    while True:
        await asyncio.sleep(3600)

# Main bot starter function
async def start_bot():
    await bot.start()
    register_commands(bot)  # Register /start and /news handlers
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()
    logging.info("Bot started and scheduler running.")
    await idle()

if __name__ == "__main__":
    asyncio.run(start_bot())
