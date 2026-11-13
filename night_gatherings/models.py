from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from dorm_heiat.models import UnitContent
from reports_media.assets import UPLOAD_HELP, extension, validate_cover, validate_embed, validate_upload


def upload_path(instance, filename):
    return f'night_gatherings/{uuid4().hex}{extension(filename)}'


class Gathering(UnitContent):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس'
        PUBLISHED = 'published', 'منتشرشده'
        HELD = 'held', 'برگزارشده'
        HIDDEN = 'hidden', 'خارج از نمایش عمومی'

    title = models.CharField('عنوان', max_length=200)
    description = models.TextField('توضیحات و شرح برنامه')
    starts_at = models.DateTimeField('تاریخ و ساعت برگزاری', db_index=True)
    venue = models.CharField('محل برگزاری', max_length=240)
    guests = models.CharField('سخنران، مداح یا مهمان', max_length=250, blank=True)
    poster = models.FileField('پوستر', upload_to=upload_path, validators=[validate_cover], blank=True)
    status = models.CharField('وضعیت', max_length=12, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ('-starts_at', '-pk')
        verbose_name = 'تجمع شبانه'
        verbose_name_plural = 'تجمعات شبانه'
        permissions = [('publish_gathering', 'Can publish or hide night gatherings')]

    def __str__(self):
        return self.title

    @classmethod
    def visible(cls):
        return cls.objects.filter(status__in=(cls.Status.PUBLISHED, cls.Status.HELD),
                                  units__isnull=False).distinct()

    def get_absolute_url(self):
        return reverse('night_gatherings:detail', args=[self.pk])


class GatheringContent(models.Model):
    title = models.CharField('عنوان', max_length=200)
    description = models.TextField('متن')
    published = models.BooleanField('منتشرشده', default=False)
    published_at = models.DateTimeField('زمان انتشار', default=timezone.now)

    class Meta:
        abstract = True
        ordering = ('-published_at', '-pk')

    def __str__(self):
        return self.title

    @classmethod
    def visible(cls):
        return cls.objects.filter(gathering__in=Gathering.visible(), published=True,
                                  published_at__lte=timezone.now())


class GatheringNotice(GatheringContent):
    gathering = models.ForeignKey(Gathering, models.CASCADE, related_name='notices', verbose_name='تجمع')
    starts_at = models.DateTimeField('زمان اعلام‌شده', null=True, blank=True)
    venue = models.CharField('محل اعلام‌شده', max_length=240, blank=True)
    poster = models.FileField('پوستر اطلاعیه', upload_to=upload_path, validators=[validate_cover], blank=True)

    class Meta(GatheringContent.Meta):
        verbose_name = 'اطلاعیهٔ تجمع'
        verbose_name_plural = 'اطلاعیه‌های تجمعات'
        permissions = [('publish_gatheringnotice', 'Can publish night gathering notices')]


class GatheringReport(GatheringContent):
    gathering = models.ForeignKey(Gathering, models.CASCADE, related_name='reports', verbose_name='تجمع')
    summary = models.TextField('شرح کوتاه', max_length=600, blank=True)

    class Meta(GatheringContent.Meta):
        verbose_name = 'گزارش تجمع'
        verbose_name_plural = 'گزارش‌های تجمعات'
        permissions = [('publish_gatheringreport', 'Can publish night gathering reports')]

    @classmethod
    def visible(cls):
        return super().visible().filter(gathering__starts_at__lte=timezone.now())


class ReportAsset(models.Model):
    report = models.ForeignKey(GatheringReport, models.CASCADE, related_name='assets', verbose_name='گزارش')
    file = models.FileField('فایل', upload_to=upload_path, validators=[validate_upload],
                            help_text=UPLOAD_HELP, blank=True)
    embed = models.CharField('پیوند یا کد iframe', max_length=3000, validators=[validate_embed], blank=True)
    caption = models.CharField('عنوان رسانه', max_length=200, blank=True)
    order = models.PositiveIntegerField('ترتیب', default=0)

    class Meta:
        ordering = ('order', 'pk')
        verbose_name = 'پیوست گزارش'
        verbose_name_plural = 'پیوست‌های گزارش'

    def clean(self):
        super().clean()
        if not self.file and not self.embed:
            raise ValidationError('فایل یا پیوند رسانه را وارد کنید.')
