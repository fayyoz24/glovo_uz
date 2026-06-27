from rest_framework.exceptions import APIException
from rest_framework import status


class PaymentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "To'lov xatosi yuz berdi."
    default_code = "payment_error"


class InsufficientWalletBalance(PaymentException):
    default_detail = "Hamyonda mablag' yetarli emas."
    default_code = "insufficient_balance"


class WalletMaxBalanceExceeded(PaymentException):
    default_detail = "Hamyon limiti oshib ketdi."
    default_code = "wallet_max_balance_exceeded"


class InvalidCardNumber(PaymentException):
    default_detail = "Karta raqami noto'g'ri."
    default_code = "invalid_card_number"


class CardNotFound(PaymentException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Karta topilmadi."
    default_code = "card_not_found"


class PaymentNotFound(PaymentException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "To'lov topilmadi."
    default_code = "payment_not_found"


class PaymentAlreadyCompleted(PaymentException):
    default_detail = "To'lov allaqachon bajarilgan."
    default_code = "payment_already_completed"


class PaymentAlreadyCancelled(PaymentException):
    default_detail = "To'lov allaqachon bekor qilingan."
    default_code = "payment_already_cancelled"


class RefundNotAllowed(PaymentException):
    default_detail = "Qaytarish mumkin emas (vaqt o'tdi yoki holat noto'g'ri)."
    default_code = "refund_not_allowed"


class RefundAmountExceeded(PaymentException):
    default_detail = "Qaytarish summasi to'lov summasidan oshib ketdi."
    default_code = "refund_amount_exceeded"


class GatewayException(PaymentException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "To'lov tizimi bilan bog'liq xato."
    default_code = "gateway_error"


class PaymeException(GatewayException):
    default_detail = "Payme tizimida xato yuz berdi."
    default_code = "payme_error"


class ClickException(GatewayException):
    default_detail = "Click tizimida xato yuz berdi."
    default_code = "click_error"


class UPayException(GatewayException):
    default_detail = "UPAY tizimida xato yuz berdi."
    default_code = "upay_error"


class PaymentSessionExpired(PaymentException):
    default_detail = "To'lov sessiyasi muddati tugagan."
    default_code = "payment_session_expired"


class DuplicateTransaction(PaymentException):
    default_detail = "Bu tranzaksiya allaqachon mavjud."
    default_code = "duplicate_transaction"


class TopUpAmountInvalid(PaymentException):
    default_detail = "To'ldirish summasi chegaralardan tashqarida."
    default_code = "top_up_amount_invalid"


class WithdrawalAmountInvalid(PaymentException):
    default_detail = "Yechib olish summasi chegaralardan tashqarida."
    default_code = "withdrawal_amount_invalid"
