import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("public_id", models.CharField(editable=False, max_length=12, unique=True)),
                ("order_id", models.UUIDField(db_index=True)),
                (
                    "complaint_type",
                    models.CharField(
                        choices=[
                            ("order_issue", "Order Issue"),
                            ("wrong_item", "Wrong Item"),
                            ("missing_item", "Missing Item"),
                            ("late_delivery", "Late Delivery"),
                            ("courier_behavior", "Courier Behavior"),
                            ("merchant_behavior", "Merchant Behavior"),
                            ("payment_issue", "Payment Issue"),
                            ("app_bug", "App Bug"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=30,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("urgent", "Urgent"),
                        ],
                        default="medium",
                        max_length=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("in_review", "In Review"),
                            ("pending_user", "Pending User Response"),
                            ("resolved", "Resolved"),
                            ("closed", "Closed"),
                            ("rejected", "Rejected"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("subject", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("internal_note", models.TextField(blank=True, default="")),
                ("resolution_note", models.TextField(blank=True, default="")),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_complaints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="complaints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "support_complaint", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ComplaintMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("body", models.TextField()),
                (
                    "attachment",
                    models.FileField(blank=True, null=True, upload_to="support/attachments/"),
                ),
                ("is_internal", models.BooleanField(default=False)),
                (
                    "sender_type",
                    models.CharField(
                        choices=[
                            ("customer", "Customer"),
                            ("support", "Support Agent"),
                            ("system", "System"),
                        ],
                        default="customer",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "complaint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="support.complaint",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="support_messages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "support_complaint_message", "ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="Dispute",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("order_id", models.UUIDField(db_index=True)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("under_investigation", "Under Investigation"),
                        ("resolved_refund", "Resolved with Refund"),
                        ("resolved_no_refund", "Resolved without Refund"),
                        ("escalated", "Escalated"),
                        ("closed", "Closed"),
                    ],
                    default="pending",
                    max_length=30,
                )),
                ("description", models.TextField()),
                ("resolution_note", models.TextField(blank=True, default="")),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="handled_disputes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "complaint",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="dispute",
                        to="support.complaint",
                    ),
                ),
                (
                    "raised_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="disputes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "support_dispute", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="RefundRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("order_id", models.UUIDField(db_index=True)),
                ("reason", models.CharField(
                    choices=[
                        ("missing_item", "Missing Item"),
                        ("wrong_item", "Wrong Item"),
                        ("quality_issue", "Quality Issue"),
                        ("late_delivery", "Late Delivery"),
                        ("order_cancelled", "Order Cancelled"),
                        ("duplicate_payment", "Duplicate Payment"),
                        ("other", "Other"),
                    ],
                    max_length=30,
                )),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("approved", "Approved"),
                        ("rejected", "Rejected"),
                        ("processed", "Processed"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("review_note", models.TextField(blank=True, default="")),
                ("payment_refund_id", models.UUIDField(blank=True, null=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "complaint",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="refund_request",
                        to="support.complaint",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="refund_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_refund_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "support_refund_request", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["order_id"], name="support_com_order_id_idx"),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["customer", "status"], name="support_com_cust_status_idx"),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["status", "created_at"], name="support_com_status_ca_idx"),
        ),
        migrations.AddIndex(
            model_name="complaint",
            index=models.Index(fields=["assigned_to", "status"], name="support_com_agent_status_idx"),
        ),
        migrations.AddIndex(
            model_name="complaintmessage",
            index=models.Index(fields=["complaint", "created_at"], name="support_msg_comp_ca_idx"),
        ),
        migrations.AddIndex(
            model_name="dispute",
            index=models.Index(fields=["order_id"], name="support_disp_order_id_idx"),
        ),
        migrations.AddIndex(
            model_name="dispute",
            index=models.Index(fields=["status", "created_at"], name="support_disp_status_ca_idx"),
        ),
        migrations.AddIndex(
            model_name="refundrequest",
            index=models.Index(fields=["order_id"], name="support_ref_order_id_idx"),
        ),
        migrations.AddIndex(
            model_name="refundrequest",
            index=models.Index(fields=["customer", "status"], name="support_ref_cust_status_idx"),
        ),
        migrations.AddIndex(
            model_name="refundrequest",
            index=models.Index(fields=["status", "created_at"], name="support_ref_status_ca_idx"),
        ),
    ]
