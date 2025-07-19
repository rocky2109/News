import os
import asyncio
import requests
from pyrogram import Client, filters
from datetime import datetime
import pytz

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
NEWS_CHANNEL = os.environ.get("NEWS_CHANNEL")  # Can be username or channel ID

# Auto-convert channel ID if it's int string
try:
    if NEWS_CHANNEL.startswith("-100"):
        NEWS_CHANNEL = int(NEWS_CHANNEL)
except:
    pass

app = Client("news_fetcher_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Custom /start message
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_photo(
        photo="https://telegra.ph/file/7cf2be234fca9bb6d33c7.jpg",  # Replace with your own
        caption=f"""<b>📰 Welcome to the Indian News Bot 🇮🇳</b>

This bot fetches live trending news headlines every few minutes and posts them to your configured Telegram channel.

➕ Stay updated with national & international stories in real-time.

<b>🛠 Maintained by:</b> <a href="tg://user?id={OWNER_ID}">Owner</a>""",
        reply_markup=None
    )

# News fetch + send function
async def fetch_and_send_news():
    while True:
        try:
            print("⏳ Fetching news...")
            url = "https://newsapi.org/v2/top-headlines?country=in&apiKey=0730e33a5fe740799cc6350667db3c4e"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                if "articles" in data and len(data["articles"]) > 0:
                    article = data["articles"][0]
                    title = article.get("title", "No Title")
                    description = article.get("description", "No Description")
                    url_link = article.get("url", "")
                    image_url = article.get("urlToImage", None)

                    now_ist = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y | %I:%M %p")

                    text = f"🗞️ <b>{title}</b>\n\n🧾 {description}\n\n🔗 <a href='{url_link}'>Read Full</a>\n🕒 {now_ist}"

                    if image_url:
                        await app.send_photo(chat_id=NEWS_CHANNEL, photo=image_url, caption=text)
                    else:
                        await app.send_message(chat_id=NEWS_CHANNEL, text=text)
                else:
                    await app.send_message(chat_id=OWNER_ID, text="⚠️ No articles found.")
            else:
                await app.send_message(chat_id=OWNER_ID, text=f"❌ Failed to fetch news.\nStatus: {response.status_code}")
        except Exception as e:
            await app.send_message(chat_id=OWNER_ID, text=f"⚠️ Error occurred:\n{e}")

        await asyncio.sleep(120)  # fetch every 2 minutes (for testing)

# Run the bot
async def main():
    await app.start()
    print("✅ Bot Started")

    # ✅ Send started message to OWNER
    try:
        await app.send_message(
            OWNER_ID,
            "✅ <b>Bot started successfully!</b>\nNews updates will be sent every 2 minutes. 📰"
        )
    except Exception as e:
        print(f"Failed to send start message to owner: {e}")

    asyncio.create_task(fetch_and_send_news())
    await app.idle()

