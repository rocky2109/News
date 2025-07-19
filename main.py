import asyncio
import logging
import requests
from typing import List
from pyrogram import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import API_ID, API_HASH, BOT_TOKEN, NEWS_API_KEY, TARGET_CHAT_ID
from commands import register_commands
from pyrogram import filters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize bot and scheduler
bot = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    user = message.from_user
    await message.reply_photo(
        photo="https://telegra.ph/file/e870b574fd3a87560a882.jpg",  # Optional banner image
        caption=f"""<b>👋 Hello {user.mention}!

🗞️ Welcome to the Auto News Bot!

🔔 This bot automatically fetches and posts news updates every 30 minutes to your linked channel.

✨ You can sit back and relax while we keep your audience updated with fresh content.</b>""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📰 Send Test News", callback_data="send_test_news")],
            [InlineKeyboardButton("📊 Check Status", callback_data="check_status")],
            [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/YOUR_CHANNEL")],
        ])
    )
@bot.on_callback_query()
async def handle_buttons(client, callback_query):
    data = callback_query.data

    if data == "send_test_news":
        news = get_latest_news()
        for msg in news:
            await callback_query.message.reply(msg)
        await callback_query.answer("✅ Sent test news")

    elif data == "check_status":
        await callback_query.answer("✅ Bot is running & scheduler is active", show_alert=True)

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply(
        "<b>🤖 Bot Commands:\n\n/start</b> – Show welcome panel\n<b>/help</b> – Show this help\n<b>/ping</b> – Check if bot is online"
    )


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
    news = get_latest_news()
    for msg in news:
        try:
            # Send to channel/group
            await bot.send_message(TARGET_CHAT_ID, msg, disable_web_page_preview=False)
            
            # Send to bot owner’s PM
            await bot.send_message(OWNER_ID, msg, disable_web_page_preview=False)
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
