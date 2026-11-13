from pathlib import PurePath
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from dorm_heiat.models import UnitContent


def banner_path(instance, filename):
    return f'campaign_banners/{uuid4().hex}{PurePath(filename).suffix.lower()}'


def banner_size(file):
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('حجم بنر نباید بیش از ۵ مگابایت باشد.')


class VolunteerSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    enabled = models.BooleanField('فرم فعال است', default=False)
    require_birth_date = models.BooleanField('تاریخ تولد اجباری است', default=True)
    require_skills = models.BooleanField('مهارت‌ها یا سوابق اجباری است', default=False)
    require_availability = models.BooleanField('روزها یا شیفت‌ها اجباری است', default=False)

    class Meta:
        verbose_name = 'تنظیمات فرم خادمی'
        verbose_name_plural = 'تنظیمات فرم خادمی'
        constraints = [models.CheckConstraint(condition=Q(id=1), name='volunteer_settings_singleton')]

    def __str__(self):
        return str(self._meta.verbose_name)


class VolunteerSection(models.Model):
    name = models.CharField('نام بخش', max_length=120, unique=True)
    active = models.BooleanField('قابل انتخاب', default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'بخش خادمی'
        verbose_name_plural = 'بخش‌های خادمی'

    def __str__(self):
        return self.name


class VolunteerApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار بررسی'
        APPROVED = 'approved', 'تأییدشده'
        REJECTED = 'rejected', 'ردشده'

    first_name = models.CharField('نام', max_length=100)
    last_name = models.CharField('نام خانوادگی', max_length=100)
    phone = models.CharField('شماره تماس', max_length=11)
    national_id = models.CharField('کد ملی', max_length=10)
    birth_date = models.DateField('تاریخ تولد', blank=True, null=True)
    skills = models.TextField('مهارت‌ها یا سوابق مرتبط', max_length=2000, blank=True)
    section = models.ForeignKey(VolunteerSection, models.PROTECT, verbose_name='بخش موردعلاقه')
    availability = models.TextField('روزها یا شیفت‌های پیشنهادی', max_length=1000, blank=True)
    status = models.CharField('وضعیت', max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField('زمان ثبت', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'درخواست خادمی'
        verbose_name_plural = 'درخواست‌های خادمی'
        permissions = [('export_volunteerapplication', 'Can export volunteer applications')]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Campaign(UnitContent):
    class Status(models.TextChoices):
        INACTIVE = 'inactive', 'غیرفعال'
        ACTIVE = 'active', 'فعال'
        FINISHED = 'finished', 'پایان‌یافته'

    class Participation(models.TextChoices):
        FORM = 'form', 'فرم داخلی'
        INSTRUCTIONS = 'instructions', 'راهنمای مشارکت بدون فرم'

    title = models.CharField('عنوان', max_length=180)
    description = models.TextField('توضیحات')
    banner = models.ImageField(
        'بنر', upload_to=banner_path, blank=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']), banner_size],
        help_text='JPG، PNG یا WebP تا ۵ مگابایت.',
    )
    starts_on = models.DateField('تاریخ شروع')
    ends_on = models.DateField('تاریخ پایان')
    status = models.CharField('وضعیت', max_length=12, choices=Status.choices, default=Status.INACTIVE)
    participation = models.CharField('شیوهٔ مشارکت', max_length=12, choices=Participation.choices,
                                     default=Participation.FORM)
    instructions = models.TextField('راهنمای مشارکت', blank=True)

    class Meta:
        ordering = ['-starts_on', '-pk']
        verbose_name = 'پویش'
        verbose_name_plural = 'پویش‌ها'
        constraints = [models.CheckConstraint(condition=Q(ends_on__gte=F('starts_on')), name='campaign_valid_dates')]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('registrations_campaigns:detail', args=[self.pk])

    def clean(self):
        super().clean()
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({'ends_on': 'تاریخ پایان نباید قبل از تاریخ شروع باشد.'})
        if self.participation == self.Participation.INSTRUCTIONS and not self.instructions.strip():
            raise ValidationError({'instructions': 'برای مشارکت بدون فرم، راهنما را وارد کنید.'})

    @property
    def is_open(self):
        return self.status == self.Status.ACTIVE and self.starts_on <= timezone.localdate() <= self.ends_on

    @property
    def public_status(self):
        today = timezone.localdate()
        if self.status == self.Status.FINISHED or self.ends_on < today:
            return 'پایان‌یافته'
        return 'شروع نشده' if self.starts_on > today else 'فعال'


class CampaignField(models.Model):
    class Kind(models.TextChoices):
        TEXT = 'text', 'متن کوتاه'
        LONG_TEXT = 'long_text', 'متن بلند'
        CHOICE = 'choice', 'انتخاب یک گزینه'
        YES_NO = 'yes_no', 'بله یا خیر'

    campaign = models.ForeignKey(Campaign, models.CASCADE, related_name='fields', verbose_name='پویش')
    label = models.CharField('عنوان فیلد', max_length=120)
    kind = models.CharField('نوع فیلد', max_length=12, choices=Kind.choices, default=Kind.TEXT)
    required = models.BooleanField('اجباری', default=False)
    options = models.TextField('گزینه‌ها', max_length=2000, blank=True, help_text='هر گزینه را در یک سطر وارد کنید.')
    order = models.PositiveSmallIntegerField('ترتیب', default=0)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'فیلد فرم پویش'
        verbose_name_plural = 'فیلدهای فرم پویش'

    def __str__(self):
        return self.label

    def option_values(self):
        return list(dict.fromkeys(line.strip() for line in self.options.splitlines() if line.strip()))

    def clean(self):
        super().clean()
        if self.kind == self.Kind.CHOICE and len(self.option_values()) < 2:
            raise ValidationError({'options': 'دست‌کم دو گزینهٔ متفاوت وارد کنید.'})


class CampaignEntry(models.Model):
    campaign = models.ForeignKey(Campaign, models.PROTECT, related_name='entries', verbose_name='پویش')
    full_name = models.CharField('نام و نام خانوادگی', max_length=160)
    phone = models.CharField('شماره تماس', max_length=11)
    answers = models.JSONField('پاسخ‌ها', default=list, editable=False)
    created_at = models.DateTimeField('زمان ثبت', auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'مشارکت‌کنندهٔ پویش'
        verbose_name_plural = 'مشارکت‌کنندگان پویش‌ها'
        permissions = [('export_campaignentry', 'Can export campaign entries')]

    def __str__(self):
        return self.full_name
