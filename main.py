import asyncio
import logging
import requests
import os
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
from pyrogram.types import Message, InputMediaPhoto

# --- Config ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Initialize bot and scheduler ---
bot = Client("news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()

from pyrogram import Client, filters

@bot.on_message(filters.command("start") & (filters.private | filters.group | filters.channel))
async def start(bot, m: Message):
    # Support anonymous admins or channels
    user_name = (
        m.from_user.first_name if m.from_user
        else m.sender_chat.title if m.sender_chat
        else "User"
    )
    sender_id = (
        m.from_user.id if m.from_user
        else m.sender_chat.id if m.sender_chat
        else m.chat.id
    )

    start_message = await bot.send_message(
        m.chat.id,
        f">**Hey 💖 {user_name}!** 👑\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f">**🦋 Welcome {user_name}!** 🦋\n\n" +
        f"Initializing Uploader bot... 🤖\n\n"
        f"Progress:\n 🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍 0%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f">🦋** Welcome {user_name}!**🦋\n\n" +
        f"Loading features... ⏳\n\n"
        f"Progress:\n ❤️❤️❤️🤍🤍🤍🤍🤍🤍🤍 25%\n\n"
    )
    
    await asyncio.sleep(1)
    await start_message.edit_text(
        f"> 🦋 ** Welcome {user_name}!** 🦋\n\n" +
        f"This may take a moment 😉\n\n"
        f"Progress:\n 🧡🧡🧡🧡🧡🤍🤍🤍🤍🤍 50%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f">🦋 **Welcome {user_name}!** 🦋\n\n" +
        f"Checking subscription status... 🔍\n\n"
        f"Progress:\n 💛💛💛💛💛💛💛💛🤍🤍 75%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f">🦋 **Welcome {user_name}!** 🦋\n\n" +
        f"Verifying access... 🔓\n\n"
        f"Progress:\n 💚💚💚💚💚💚💚💚💚💚 100%\n\n"
    )


    await asyncio.sleep(2)
    if m.chat.id in AUTH_USERS:
        await start_message.edit_text(
            f"✅ Access Granted 😉\n\n"
            f">👑 **Hey {m.from_user.first_name}!** \n\n"
            f"💎 You are an <b>Authorized User Cutie</b> 😘\n\n"
            f"➠ Use /xtract to extract from .txt (Auto 🚀)\n\n"
            f"➠ Use /help for full guide 📖\n\n"
            f">Creator: [𝗖𝗛𝗢𝗦𝗘𝗡 𝗢𝗡𝗘 ⚝](http://t.me/CHOSEN_ONEx_bot)\n", disable_web_page_preview=True, reply_markup=BUTTONSCONTACT
        )
        
    else:
        await asyncio.sleep(2)
        await start_message.edit_text(
            f"> Hey Dear {m.from_user.first_name}!\n\n"
            f"thanks for being with us 😊\n\n"
            f"➠ Use /xtract to extract from .txt (Auto 🚀)\n"
            f"➠ Use /help for full guide 📖\n\n"            
            f">Creator: [𝗖𝗛𝗢𝗦𝗘𝗡 𝗢𝗡𝗘 ⚝](http://t.me/CHOSEN_ONEx_bot)\n", disable_web_page_preview=True, reply_markup=BUTTONSCONTACT
        )

# --- Help command ---
@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply(
        "<b>🤖 Bot Commands:\n/start</b> – Show welcome panel\n<b>/help</b> – Show help\n<b>/ping</b> – Check online status"
    )

# --- Button callbacks ---
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

# --- Fetch news ---
def get_latest_news() -> List[str]:
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    headers = {"User-Agent": "TelegramNewsBot/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])[:5]
        return [
            f"📰 <b>{a.get('title')}</b>\n\n{a.get('description')}\n🔗 <a href='{a.get('url')}'>Read More</a>"
            for a in articles
        ]
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return ["❌ Failed to fetch news."]

# --- Send news job ---
async def send_news():
    logging.info("Sending news...")
    news = get_latest_news()
    for msg in news:
        try:
            await bot.send_message(TARGET_CHAT_ID, msg, disable_web_page_preview=False)
            await bot.send_message(OWNER_ID, msg, disable_web_page_preview=False)
        except Exception as e:
            logging.error(f"Error sending news: {e}")

# --- Notify owner on restart ---
async def notify_owner():
    try:
        await bot.send_message(chat_id=OWNER_ID, text="✅ Bot restarted and is now running.")
    except RPCError as e:
        logging.error(f"Failed to notify owner: {e}")

# --- Start everything ---
async def main():
    await bot.start()
    await notify_owner()
    scheduler.add_job(send_news, "interval", minutes=2)
    scheduler.start()
    logging.info("Bot started. Scheduler is running.")
    await idle()

# --- Run bot ---
async def idle():
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
