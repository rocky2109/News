import os
import asyncio
from datetime import datetime
import pytz
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Set timezone to India
IST = pytz.timezone("Asia/Kolkata")

# Environment variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
NEWS_CHANNEL = os.environ.get("NEWS_CHANNEL")  # e.g., -1001234567890

# Pyrogram app
app = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    await message.reply_photo(
        photo="https://te.legra.ph/file/4d5e189f3d661fac9bfc6.jpg",
        caption="""
👋 <b>Welcome to the Daily News Bot!</b>

📰 Get the latest technology headlines every 2 minutes (for testing).

⚙️ This bot automatically posts tech news in the linked channel.
        """,
    )


async def fetch_and_send_news():
    while True:
        try:
            url = "https://inshortsapi.vercel.app/news?category=technology"
            response = requests.get(url)
            data = response.json()

            if data.get("success") and "data" in data:
                articles = data["data"][:1]  # Send only the latest 1 article
                for article in articles:
                    time_now = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")
                    text = f"""
<b>📰 {article['title']}</b>

{article['content']}

🕒 {time_now}
🔗 {article.get('readMoreUrl', 'N/A')}
"""
                    await app.send_photo(chat_id=NEWS_CHANNEL, photo=article["imageUrl"], caption=text)
                    print(f"✅ Sent news at {time_now}")
            else:
                await app.send_message(chat_id=NEWS_CHANNEL, text="❌ Failed to fetch news from API.")

        except Exception as e:
            error_time = datetime.now(IST).strftime("%d-%m-%Y %I:%M %p")
            await app.send_message(chat_id=NEWS_CHANNEL, text=f"⚠️ Error at {error_time}:\n{e}")
            print(f"❌ Error: {e}")

        await asyncio.sleep(120)  # 2 minutes


async def main():
    await app.start()
    print("✅ Bot started.")
    await fetch_and_send_news()


if __name__ == "__main__":
    asyncio.run(main())
