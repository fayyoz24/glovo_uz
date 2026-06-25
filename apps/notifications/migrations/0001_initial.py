"""
Run: python manage.py makemigrations notifications
Then: python manage.py migrate

Below is a reference migration (auto-generated will look similar).
"""
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceToken",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("token", models.TextField()),
                ("provider", models.CharField(choices=[("fcm", "Firebase Cloud Messaging"), ("apns", "Apple Push Notification Service")], default="fcm", max_length=20)),
                ("device_id", models.CharField(blank=True, help_text="Unique device identifier", max_length=255)),
                ("device_name", models.CharField(blank=True, max_length=255)),
                ("app_version", models.CharField(blank=True, max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="device_tokens", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "notification_device_tokens"},
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("push_enabled", models.BooleanField(default=True)),
                ("sms_enabled", models.BooleanField(default=True)),
                ("email_enabled", models.BooleanField(default=True)),
                ("in_app_enabled", models.BooleanField(default=True)),
                ("promotional_push", models.BooleanField(default=True)),
                ("promotional_sms", models.BooleanField(default=False)),
                ("promotional_email", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preference", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "notification_preferences"},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event", models.CharField(max_length=60)),
                ("channel", models.CharField(max_length=20)),
                ("notification_type", models.CharField(default="transactional", max_length=20)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("body", models.TextField()),
                ("data", models.JSONField(blank=True, default=dict)),
                ("push_token", models.TextField(blank=True)),
                ("phone_number", models.CharField(blank=True, max_length=20)),
                ("email_address", models.EmailField(blank=True)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("failure_reason", models.TextField(blank=True)),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("order_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("attempt_count", models.PositiveSmallIntegerField(default=0)),
                ("max_attempts", models.PositiveSmallIntegerField(default=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("recipient", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "notifications", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "channel", "status"], name="notif_user_channel_status_idx"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "event", "created_at"], name="notif_user_event_idx"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["status", "attempt_count"], name="notif_retry_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="devicetoken",
            unique_together={("user", "device_id", "provider")},
        ),
    ]
