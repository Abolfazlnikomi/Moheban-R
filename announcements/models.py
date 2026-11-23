from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from dorm_heiat.models import EditorialContent
from reports_media.assets import extension, validate_cover


def image_path(instance, filename):
    return f'announcements/{uuid4().hex}{extension(filename)}'


class Announcement(EditorialContent):
    cover = models.ImageField(
        'عکس شاخص',
        upload_to=image_path,
        validators=[validate_cover],
        blank=True,
    )
    expires_at = models.DateTimeField(
        'زمان انقضا',
        blank=True,
        null=True,
    )
    gathering = models.ForeignKey(
        'night_gatherings.Gathering',
        models.SET_NULL,
        blank=True,
        null=True,
        related_name='site_announcements',
        verbose_name='برنامهٔ مرتبط هیئت',
    )

    class Meta(EditorialContent.Meta):
        verbose_name = 'اطلاعیه'
        verbose_name_plural = 'اطلاعیه‌ها'

    def clean(self):
        super().clean()
        if self.expires_at and self.published_at and self.expires_at <= self.published_at:
            raise ValidationError({
                'expires_at': 'زمان انقضا باید بعد از زمان انتشار باشد.'
            })

    def get_absolute_url(self):
        return reverse('announcements:detail', args=[self.pk])


class AnnouncementImage(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        models.CASCADE,
        related_name='images',
    )
    file = models.ImageField(
        'تصویر',
        upload_to=image_path,
        validators=[validate_cover],
    )

    class Meta:
        ordering = ('pk',)
        verbose_name = 'تصویر اطلاعیه'
        verbose_name_plural = 'تصاویر اطلاعیه'

    def __str__(self):
        return self.file.name.rsplit('/', 1)[-1]
