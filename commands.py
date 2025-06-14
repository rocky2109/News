from pyrogram import filters
import requests
from config import NEWS_API_KEY

def register_commands(app):
    @app.on_message(filters.command("start"))
    async def start_command(client, message):
        await message.reply_text("👋 Hello! I'm a Daily News Bot.\nUse /news to get the latest headlines.")

    @app.on_message(filters.command("news"))
    async def news_command(client, message):
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
        try:
            response = requests.get(url)
            articles = response.json().get("articles", [])[:5]

            if not articles:
                await message.reply_text("😕 No news found.")
                return

            for article in articles:
                title = article.get("title", "No title")
                description = article.get("description", "")
                link = article.get("url", "")
                text = f"📰 **{title}**\n{description}\n🔗 [Read More]({link})"
                await message.reply_text(text, disable_web_page_preview=False)
        except Exception:
            await message.reply_text("❌ Error fetching news.")
