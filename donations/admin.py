
from django.contrib import admin

from .models import DonationSettings, DonationTransaction


@admin.register(DonationSettings)
class DonationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "payment_enabled",
        "updated_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("اطلاعات صفحه", {
            "fields": (
                "title",
                "description",
            )
        }),
        ("اطلاعات کارت", {
            "fields": (
                "card_image",
                "card_description",
            )
        }),
        ("تنظیمات پرداخت آنلاین", {
            "fields": (
                "payment_enabled",
                "payment_disabled_message",
            )
        }),
        ("اطلاعات زمانی", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def has_add_permission(self, request):
        return not DonationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DonationTransaction)
class DonationTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "amount",
        "status",
        "gateway",
        "user",
        "created_at",
        "paid_at",
    )

    list_filter = (
        "status",
        "gateway",
        "created_at",
    )

    search_fields = (
        "tracking_code",
        "gateway_reference",
        "authority",
        "user__username",
    )

    readonly_fields = (
        "created_at",
        "paid_at",
    )

    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False
