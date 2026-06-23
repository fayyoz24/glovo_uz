import uuid
from django.db import models
from apps.merchants.constants import MerchantType, MerchantStatus


class Merchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    type = models.CharField(max_length=20, choices=MerchantType.CHOICES, default=MerchantType.FOOD)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="merchants/logos/", null=True, blank=True)
    cover = models.ImageField(upload_to="merchants/covers/", null=True, blank=True)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=MerchantStatus.CHOICES, default=MerchantStatus.PENDING)
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="owned_merchants",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "merchants_merchant"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["type", "status"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.status == MerchantStatus.ACTIVE
