from phonenumbers import parse, format_number, PhoneNumberFormat

def normalize_phone(phone: str) -> str:
    parsed = parse(phone, "UZ")
    return format_number(parsed, PhoneNumberFormat.E164)