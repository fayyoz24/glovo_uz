class UserRole:
    CUSTOMER = "customer"
    COURIER = "courier"
    MERCHANT_OWNER = "merchant_owner"
    MERCHANT_MANAGER = "merchant_manager"
    ADMIN = "admin"
    SUPPORT = "support"

    CHOICES = [
        (CUSTOMER, "Customer"),
        (COURIER, "Courier"),
        (MERCHANT_OWNER, "Merchant Owner"),
        (MERCHANT_MANAGER, "Merchant Manager"),
        (ADMIN, "Admin"),
        (SUPPORT, "Support"),
    ]


class VehicleType:
    BICYCLE = "bicycle"
    MOTORBIKE = "motorbike"
    CAR = "car"
    FOOT = "foot"

    CHOICES = [
        (BICYCLE, "Bicycle"),
        (MOTORBIKE, "Motorbike"),
        (CAR, "Car"),
        (FOOT, "On Foot"),
    ]


class Language:
    UZ = "uz"
    RU = "ru"
    EN = "en"

    CHOICES = [
        (UZ, "Uzbek"),
        (RU, "Russian"),
        (EN, "English"),
    ]


OTP_EXPIRY_SECONDS = 120
OTP_MAX_ATTEMPTS = 5
OTP_COOLDOWN_SECONDS = 60
