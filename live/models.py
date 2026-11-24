
from django.db import models


class LiveStream(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان لایو"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    embed_url = models.URLField(
        max_length=500,
        verbose_name="لینک Embed آپارات"
    )

    is_active = models.BooleanField(
        default=False,
        verbose_name="وضعیت پخش"
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
        # فقط یک رکورد لایو در دیتابیس مجاز است
        self.pk = 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "پخش زنده"
        verbose_name_plural = "مدیریت پخش زنده"

    def __str__(self):
        return self.title
