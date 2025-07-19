import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz
from pyrogram.errors import PeerIdInvalid

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))  # Your Telegram ID
NEWS_CHANNEL = os.environ.get("NEWS_CHANNEL")  # Channel ID with -100 (as str)
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

app = Client("news_fetcher_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%d-%m-%Y %I:%M %p")

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    await message.reply(
        f"👋 Hello **{message.from_user.first_name}**!\n\n"
        "📰 I'm a **News Feed Bot** that fetches top headlines every 2 minutes.\n\n"
        "📡 News Source: [NewsAPI.org](https://newsapi.org)\n"
        "🔔 You'll receive updates here and in the news channel.\n\n"
        "**Use me in channels or check your feed here!**",
        disable_web_page_preview=True
    )

async def fetch_and_send_news():
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines?country=in&pageSize=1&apiKey={NEWS_API_KEY}"
        )
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data["articles"]:
            article = data["articles"][0]
            news_text = (
                f"🗞️ <b>{article['title']}</b>\n\n"
                f"📰 {article['description'] or ''}\n\n"
                f"🔗 <a href='{article['url']}'>Read More</a>\n"
                f"🕰️ {get_time()}"
            )

            # Send to channel
            try:
                await app.send_message(chat_id=int(NEWS_CHANNEL), text=news_text, parse_mode="html", disable_web_page_preview=False)
            except PeerIdInvalid:
                print("❌ Invalid channel ID or bot not admin!")

            # Send to Owner
            await app.send_message(chat_id=OWNER_ID, text=news_text, parse_mode="html", disable_web_page_preview=False)
        else:
            await app.send_message(OWNER_ID, text="❌ Failed to fetch news or no articles found.")
    except Exception as e:
        await app.send_message(OWNER_ID, text=f"⚠️ Error occurred:\n<code>{str(e)}</code>", parse_mode="html")

@app.on_message(filters.command("ping") & filters.user(OWNER_ID))
async def ping(_, m):
    await m.reply("✅ Bot is Alive!")

@app.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart(client, message):
    await message.reply("♻️ Restarting...")
    os.system("kill 1")

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message: Message):
    await message.reply("🆘 I fetch and send news every 2 minutes. That's all!")

# Scheduler to run news every 2 minutes
scheduler = AsyncIOScheduler()
scheduler.add_job(fetch_and_send_news, "interval", minutes=2)
scheduler.start()

@app.on_message(filters.command("news") & filters.user(OWNER_ID))
async def manual_fetch(_, m):
    await fetch_and_send_news()
    await m.reply("📩 News fetched and sent!")

# Start the bot
@app.on_message(filters.command("start_bot"))
async def notify_owner(_, __):
    await app.send_message(OWNER_ID, "✅ Bot Started and News Auto Fetching Enabled!")

app.run()
