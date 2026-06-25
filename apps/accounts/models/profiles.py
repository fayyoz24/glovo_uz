import uuid
from django.db import models
from apps.accounts.constants import VehicleType


class CustomerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    default_address = models.ForeignKey(
        "locations.Address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_customer_profile"

    def __str__(self):
        return f"CustomerProfile({self.user.phone})"


class CourierProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="courier_profile",
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.CHOICES,
        default=VehicleType.MOTORBIKE,
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_deliveries = models.PositiveIntegerField(default=0)
    is_online = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_courier_profile"
        indexes = [
            models.Index(fields=["is_online", "is_available"]),
        ]

    def __str__(self):
        return f"CourierProfile({self.user.phone})"



