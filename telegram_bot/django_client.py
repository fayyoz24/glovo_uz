"""
telegram_bot/django_client.py

Bot Django backend bilan shu modul orqali gaplashadi.
Barcha HTTP so'rovlar bu yerda — handlers clean bo'lsin.
"""
from __future__ import annotations

import logging
import requests

from telegram_bot.config import BACKEND_BASE_URL, WEBHOOK_SECRET

logger = logging.getLogger(__name__)

BASE = BACKEND_BASE_URL.rstrip("/")
HEADERS = {
    "Content-Type": "application/json",
    "X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET,
}


def confirm_telegram_link(token: str, telegram_user_id: int, telegram_username: str = "") -> bool:
    """
    Foydalanuvchi /start <token> yuborganda chaqiriladi.
    Django backend TelegramBinding ni tasdiqlaydi.

    Returns:
        True  — muvaffaqiyatli bog'landi
        False — token noto'g'ri, muddati o'tgan yoki boshqa xato
    """
    url = f"{BASE}/api/v1/auth/telegram/webhook/"
    payload = {
        "token": token,
        "telegram_user_id": telegram_user_id,
        "telegram_username": telegram_username,
    }
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            logger.info("TelegramBinding confirmed: user_id=%s token=%s", telegram_user_id, token)
            return True
        logger.warning(
            "confirm_telegram_link failed: status=%s body=%s", resp.status_code, resp.text[:200]
        )
        return False
    except requests.RequestException as exc:
        logger.exception("confirm_telegram_link network error: %s", exc)
        return False
