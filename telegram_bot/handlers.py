"""
telegram_bot/handlers.py

Barcha bot handler'lari shu yerda.

Foydalanuvchi oqimi:
  1. Django profilida "Telegram ulash" → deep link oladi:
         t.me/GlovoUZBot?start=<uuid-token>
  2. Shu linkni bosadi → bot /start <token> qabul qiladi
  3. Bot Django webhook endpoint ga POST qiladi
  4. Django TelegramBinding.is_confirmed = True qiladi
  5. Bundan keyin login paytida OTP Telegram orqali yetadi
"""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from telegram_bot.django_client import confirm_telegram_link

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────────────────────────────────────
#  /start — deep link bilan va ularsiz
# ─────────────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    /start  — oddiy boshlash (token yo'q)
    /start <token>  — Telegram akkauntni bog'lash
    """
    args = message.text.split(maxsplit=1)
    token = args[1].strip() if len(args) > 1 else None

    if not token:
        # Oddiy /start — foydalanuvchiga tushuntirish
        await message.answer(
            "👋 <b>Glovo UZ</b> botiga xush kelibsiz!\n\n"
            "Bu bot orqali:\n"
            "• Telegram akkauntingizni Glovo UZ ga bog'lashingiz\n"
            "• Login paytida OTP kodni Telegram orqali olishingiz mumkin\n\n"
            "Boshlash uchun Glovo UZ ilovasida "
            "<b>Profil → Telegram ulash</b> bo'limiga o'ting.",
            parse_mode="HTML",
        )
        return

    # Token bilan /start — TelegramBinding tasdiqlash
    user = message.from_user
    success = confirm_telegram_link(
        token=token,
        telegram_user_id=user.id,
        telegram_username=user.username or "",
    )

    if success:
        await message.answer(
            "✅ <b>Telegram muvaffaqiyatli bog'landi!</b>\n\n"
            "Endi Glovo UZ ga kirishda tasdiqlash kodini "
            "Telegram orqali olishingiz mumkin.",
            parse_mode="HTML",
        )
        logger.info("Telegram linked: user_id=%s username=%s", user.id, user.username)
    else:
        await message.answer(
            "❌ <b>Bog'lash amalga oshmadi.</b>\n\n"
            "Link eskirgan yoki allaqachon ishlatilgan bo'lishi mumkin.\n"
            "Glovo UZ ilovasida qaytadan urinib ko'ring.",
            parse_mode="HTML",
        )
        logger.warning("Telegram link failed: user_id=%s token=%s", user.id, token)


# ─────────────────────────────────────────────────────────────────────────────
#  /help
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "<b>Telegram ulash:</b>\n"
        "Glovo UZ ilova → Profil → Telegram ulash\n\n"
        "<b>Telegram ajratish:</b>\n"
        "Glovo UZ ilova → Profil → Telegram ajratish\n\n"
        "Muammo bo'lsa: <a href='https://glovo.uz/support'>Qo'llab-quvvatlash</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Boshqa xabarlar
# ─────────────────────────────────────────────────────────────────────────────

@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Bu bot faqat login uchun OTP kodlarini yuboradi.\n"
        "Yordam uchun /help buyrug'ini yuboring.",
    )
