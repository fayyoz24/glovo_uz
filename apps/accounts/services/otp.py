import uuid
from django.db import transaction

from apps.accounts.models import User, TelegramBinding
from apps.accounts.selectors.user import get_telegram_binding_by_token


def initiate_telegram_link(user: User) -> TelegramBinding:
    """
    Foydalanuvchi profilida "Telegram'ni ulash" tugmasini bosganda chaqiriladi.
    Yangi link_token yaratadi (yoki mavjudini qaytaradi).
    Frontend shu token orqali deep link ko'rsatadi: t.me/BotName?start=<token>
    """
    binding, _ = TelegramBinding.objects.get_or_create(
        user=user,
        defaults={"link_token": uuid.uuid4(), "is_confirmed": False},
    )

    # Eski tasdiqlanmagan binding bo'lsa — tokenni yangilab qo'yamiz
    if not binding.is_confirmed:
        binding.link_token = uuid.uuid4()
        binding.save(update_fields=["link_token"])

    return binding


def confirm_telegram_link(token: str, telegram_user_id: int, telegram_username: str = "") -> TelegramBinding:
    """
    Bot webhook chaqiradi: foydalanuvchi /start <token> yuborganda.
    Tokenga mos TelegramBinding topib, telegram_user_id ni saqlaydi.

    Raises:
        ValueError – token noto'g'ri yoki allaqachon tasdiqlangan
    """
    binding = get_telegram_binding_by_token(token)

    if binding is None:
        raise ValueError("Token topilmadi yoki muddati o'tgan")

    if binding.is_confirmed:
        raise ValueError("Bu token allaqachon ishlatilgan")

    with transaction.atomic():
        binding.telegram_user_id = telegram_user_id
        binding.telegram_username = telegram_username
        binding.is_confirmed = True
        binding.save(update_fields=["telegram_user_id", "telegram_username", "is_confirmed"])

    return binding


def unlink_telegram(user: User) -> None:
    """
    Foydalanuvchi Telegram'ni ajratib olmoqchi bo'lganda.
    """
    TelegramBinding.objects.filter(user=user).delete()