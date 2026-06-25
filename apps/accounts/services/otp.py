from apps.notifications.tasks import send_otp_sms

send_otp_sms.delay(phone="+998901234567", code="123456", lang="uz")