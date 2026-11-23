from uuid import uuid4

import bleach
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field  # یا ckeditor.fields.RichTextField

from dorm_heiat.models import UnitContent, discoverable

from .assets import UPLOAD_HELP, extension, resolve_embed, validate_cover, validate_embed, validate_upload


def upload_path(instance, filename):
    return f'reports_media/{uuid4().hex}{extension(filename)}'


class NamedModel(models.Model):
    name = models.CharField('نام', max_length=150, unique=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'


class Tag(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = 'برچسب'
        verbose_name_plural = 'برچسب‌ها'


class Event(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = 'مراسم یا رویداد'
        verbose_name_plural = 'مراسم‌ها و رویدادها'


class MediaPostQuerySet(models.QuerySet):
    def visible(self, archived=False):
        statuses = Q(status=MediaPost.Status.PUBLISHED)
        if archived:
            statuses |= Q(status=MediaPost.Status.ARCHIVED, show_in_archive=True)
        return discoverable(self.filter(statuses, published_at__lte=timezone.now()))


class MediaPost(UnitContent):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس'
        PENDING = 'pending', 'در انتظار تأیید'
        PUBLISHED = 'published', 'منتشرشده'
        ARCHIVED = 'archived', 'بایگانی‌شده'

    class Kind(models.TextChoices):
        REPORT = 'report', 'گزارش'
        GALLERY = 'gallery', 'گالری عکس'
        VIDEO = 'video', 'ویدیو'
        AUDIO = 'audio', 'فایل صوتی'
        MIXED = 'mixed', 'ترکیبی'

    # تگ‌های مجاز امن برای محتوای ویرایشگر CKEditor
    ALLOWED_TAGS = [
        'p', 'h2', 'h3', 'h4', 'strong', 'em', 'u', 's', 'ol', 'ul', 'li',
        'blockquote', 'a', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'br'
    ]
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target', 'rel'],
        'table': ['class'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan'],
    }

    title = models.CharField('عنوان', max_length=240)
    summary = models.TextField('خلاصه', max_length=600, help_text='چکیده مختصر که در کارت‌های آرشیو نمایش داده می‌شود.')
    description = CKEditor5Field('متن کامل گزارش', config_name='extends')
    event_date = models.DateField('تاریخ مراسم', db_index=True)
    published_at = models.DateTimeField('زمان انتشار', null=True, blank=True, help_text='برای انتشار فوری خالی بگذارید.')
    category = models.ForeignKey(Category, models.PROTECT, verbose_name='دسته‌بندی')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='برچسب‌ها')
    events = models.ManyToManyField(Event, blank=True, verbose_name='مراسم‌ها')
    kind = models.CharField('نوع محتوا', max_length=12, choices=Kind.choices)
    status = models.CharField('وضعیت', max_length=12, choices=Status.choices, default=Status.DRAFT)
    show_in_archive = models.BooleanField('نمایش عمومی پس از بایگانی', default=False)
    cover = models.FileField('تصویر شاخص', upload_to=upload_path, blank=True, validators=[validate_cover],
                             help_text='JPG، PNG یا WebP، حداکثر ۱۰ مگابایت.')
    responsible = models.CharField('مسئول محتوا', max_length=150)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True,
                                   editable=False, verbose_name='ثبت‌کننده')
    views = models.PositiveBigIntegerField('بازدید', default=0, editable=False)
    objects = MediaPostQuerySet.as_manager()

    class Meta:
        verbose_name = 'گزارش یا محتوای رسانه‌ای'
        verbose_name_plural = 'گزارش‌ها و محتواهای رسانه‌ای'
        indexes = [models.Index(fields=['status', 'published_at'])]
        permissions = [('publish_mediapost', 'Can publish or archive media posts')]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        # پاک‌سازی و کنترل امنیتی HTML تولیدشده توسط CKEditor
        if self.description:
            self.description = bleach.clean(
                self.description,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                strip=True
            )

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'published_at'}
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('reports_media:detail', args=[self.pk])


class MediaFile(models.Model):
    post = models.ForeignKey(MediaPost, models.CASCADE, related_name='attachments', verbose_name='محتوا')
    file = models.FileField('فایل بارگذاری‌شده', upload_to=upload_path, blank=True, validators=[validate_upload],
                            help_text=UPLOAD_HELP)
    embed = models.CharField('پیوند یا کد اشتراک (آپارات، یوتیوب و...)', max_length=3000, blank=True,
                             validators=[validate_embed],
                             help_text='می‌توانید لینک ویدئوی آپارات، یوتیوب یا فایل صوتی را اینجا قرار دهید.')
    caption = models.CharField('عنوان یا توضیح رسانه', max_length=200, blank=True)
    order = models.PositiveIntegerField('ترتیب نمایش', default=0)
    private = models.BooleanField('خصوصی (فقط مدیر مجاز)', default=False)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'رسانهٔ پیوست'
        verbose_name_plural = 'رسانه‌های پیوست'

    def clean(self):
        super().clean()
        if not self.file and not self.embed:
            raise ValidationError('حداقل یکی از موارد «فایل بارگذاری‌شده» یا «پیوند رسانه» باید وارد شود.')

    def __str__(self):
        return self.caption or f'رسانهٔ {self.post}'

    @property
    def online(self):
        return resolve_embed(self.embed) if self.embed else None
