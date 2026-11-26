
from django.conf import settings
from django.db import models


class DonationSettings(models.Model):
    title = models.CharField(
        max_length=200,
        default="حمایت مالی از هیئت",
        verbose_name="عنوان صفحه"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    card_image = models.ImageField(
        upload_to="donations/cards/",
        blank=True,
        null=True,
        verbose_name="تصویر شماره کارت"
    )

    card_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="توضیح زیر تصویر کارت"
    )

    payment_enabled = models.BooleanField(
        default=False,
        verbose_name="فعال بودن پرداخت آنلاین"
    )

    payment_disabled_message = models.CharField(
        max_length=300,
        default="درگاه پرداخت آنلاین در حال حاضر فعال نیست.",
        verbose_name="پیام غیرفعال بودن پرداخت"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش"
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "تنظیمات کمک مالی"
        verbose_name_plural = "تنظیمات کمک مالی"

    def __str__(self):
        return self.title


class DonationTransaction(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        SUCCESS = "success", "پرداخت موفق"
        FAILED = "failed", "پرداخت ناموفق"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donation_transactions",
        verbose_name="کاربر"
    )

    amount = models.PositiveBigIntegerField(
        verbose_name="مبلغ (تومان)"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="وضعیت تراکنش"
    )

    gateway = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="درگاه پرداخت"
    )

    authority = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="شناسه درخواست درگاه"
    )

    tracking_code = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="کد پیگیری"
    )

    gateway_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="شناسه مرجع درگاه"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ پرداخت"
    )

    class Meta:
        verbose_name = "تراکنش کمک مالی"
        verbose_name_plural = "تراکنش‌های کمک مالی"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.amount:,} تومان - {self.get_status_display()}"
