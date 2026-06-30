"""
telegram_bot/config.py

Bot uchun konfiguratsiya — .env dan o'qiladi.
"""
from decouple import config

BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET: str = config("TELEGRAM_WEBHOOK_SECRET")

# Django backend base URL (webhook orqali confirm qilish uchun)
BACKEND_BASE_URL: str = config("BACKEND_BASE_URL", default="http://localhost:8000")

# Bot o'z webhook URL si (Telegram'ga register qilish uchun)
# Masalan: https://api.yourdomain.uz/api/v1/auth/telegram/webhook/
WEBHOOK_URL: str = config("TELEGRAM_WEBHOOK_URL", default="")
