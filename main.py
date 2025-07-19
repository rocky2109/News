import os
import asyncio
import pytz
import requests
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

# Load from .env if needed
NEWS_CHANNEL = int(os.getenv("NEWS_CHANNEL", "-100XXXXXXXXXX"))  # Replace or set via environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "12345"))
API_HASH = os.getenv("API_HASH", "your_api_hash")

# IST timezone
IST = pytz.timezone("Asia/Kolkata")

# Initialize bot
app = Client("newsbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /start command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply_text(
        "**📰 Welcome to the NewsBot!**\n\n"
        "This bot auto-posts news headlines to a channel.\n"
        "Check back soon for updates. 😊",
        quote=True
    )

# Function to fetch and post news
async def fetch_and_send_news():
    while True:
        try:
            now = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")

            # Replace this URL with your real API
            response = requests.get("https://inshortsapi.vercel.app/news?category=technology")

            if response.status_code == 200 and response.content:
                news_data = response.json()
                news_list = news_data.get("data", [])

                if news_list:
                    for news in news_list[:3]:  # Post only top 3 for testing
                        title = news.get("title")
                        content = news.get("content")
                        read_more = news.get("read_more_url") or ""
                        url_part = f"\n🔗 [Read More]({read_more})" if read_more else ""

                        text = (
                            f"🗞️ **{title}**\n\n"
                            f"{content}{url_part}\n\n"
                            f"🕒 {now} (IST)"
                        )

                        await app.send_message(
                            chat_id=NEWS_CHANNEL,
                            text=text,
                            disable_web_page_preview=True
                        )
                else:
                    await app.send_message(chat_id=NEWS_CHANNEL, text="⚠️ No news found.")

            else:
                await app.send_message(chat_id=NEWS_CHANNEL, text=f"❌ Failed to fetch news.\nStatus: {response.status_code}")

        except Exception as e:
            await app.send_message(chat_id=NEWS_CHANNEL, text=f"⚠️ Error occurred:\n{str(e)}")

        await asyncio.sleep(120)  # Wait 2 minutes

# Start the bot and the news loop
async def main():
    await app.start()
    asyncio.create_task(fetch_and_send_news())
    print("✅ Bot Started")
    await idle()
    await app.stop()

from pyrogram import idle

if __name__ == "__main__":
    asyncio.run(main())
