import os

API_ID = int(os.environ.get("API_ID", "10720863"))
API_HASH = os.environ.get("API_HASH", "2405be04691f86d83e96bdc7c54feb1c")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7202774752:AAFkSrcu8OLIhu_aeu3CT8Y2-6inb3hj1JA")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "db677b89fa1843a5bf39d6681bed1405")
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", "-1002526234630"))  # Where to send news
