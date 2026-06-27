from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    PROCESSING = "processing", "Jarayonda"
    COMPLETED = "completed", "Bajarildi"
    FAILED = "failed", "Muvaffaqiyatsiz"
    REFUNDED = "refunded", "Qaytarildi"
    PARTIALLY_REFUNDED = "partially_refunded", "Qisman qaytarildi"
    CANCELLED = "cancelled", "Bekor qilindi"


class PaymentMethod(models.TextChoices):
    PAYME = "payme", "Payme"
    CLICK = "click", "Click"
    UPAY = "upay", "UPAY (UzCard/Humo)"
    CASH = "cash", "Naqd pul"
    WALLET = "wallet", "Hamyon"


class TransactionType(models.TextChoices):
    PAYMENT = "payment", "To'lov"
    REFUND = "refund", "Qaytarish"
    TOP_UP = "top_up", "Hamyon to'ldirish"
    WITHDRAWAL = "withdrawal", "Yechib olish"
    CASHBACK = "cashback", "Cashback"


class WalletTransactionStatus(models.TextChoices):
    PENDING = "pending", "Kutilmoqda"
    COMPLETED = "completed", "Bajarildi"
    FAILED = "failed", "Muvaffaqiyatsiz"
    REVERSED = "reversed", "Qaytarildi"


class CardType(models.TextChoices):
    UZCARD = "uzcard", "UzCard"
    HUMO = "humo", "Humo"
    VISA = "visa", "Visa"
    MASTERCARD = "mastercard", "Mastercard"


# Gateway endpoints
PAYME_BASE_URL = "https://checkout.paycom.uz/api"
CLICK_BASE_URL = "https://api.click.uz/v2/merchant"
UPAY_BASE_URL = "https://upay.uz/api/v1"

# Min/Max wallet balance (UZS)
WALLET_MIN_BALANCE = 0
WALLET_MAX_BALANCE = 50_000_000  # 50 mln UZS

# Min top-up / withdrawal amounts (UZS)
MIN_TOP_UP_AMOUNT = 1_000
MAX_TOP_UP_AMOUNT = 10_000_000

MIN_WITHDRAWAL_AMOUNT = 10_000
MAX_WITHDRAWAL_AMOUNT = 5_000_000

# Luhn check prefix map
UZCARD_PREFIX = "8600"
HUMO_PREFIX = "9860"

# Refund window (hours)
REFUND_WINDOW_HOURS = 24

# Cashback percentage (default)
DEFAULT_CASHBACK_PERCENT = 0  # 0% unless promo

# Payment session expiry (minutes)
PAYMENT_SESSION_EXPIRY_MINUTES = 15
