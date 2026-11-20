from django.core.validators import URLValidator
from django.db import models


web_link = URLValidator(schemes=['https', 'http'])


class FooterSettings(models.Model):
    name = models.CharField('نام هیئت', max_length=150, default='هیئت محبان اهل‌بیت علیهم‌السلام')
    about = models.TextField('معرفی هیئت', blank=True, default='پایگاه فرهنگی و مذهبی محبان')
    goals = models.TextField('اهداف', blank=True)
    activities = models.TextField('فعالیت‌ها', blank=True)
    contact = models.TextField('توضیحات تماس', blank=True)
    phone = models.CharField('شماره تماس', max_length=80, blank=True)
    email = models.EmailField('ایمیل', blank=True)
    address = models.TextField('نشانی', blank=True)
    channel_url = models.URLField('لینک کانال اصلی', blank=True, validators=[web_link])
    instagram_url = models.URLField('لینک اینستاگرام', blank=True, validators=[web_link])

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(pk=1), name='site_info_single_footer')]
        verbose_name = 'اطلاعات فوتر'
        verbose_name_plural = 'اطلاعات فوتر'

    def __str__(self):
        return self.name


class SocialLink(models.Model):
    footer = models.ForeignKey(FooterSettings, models.CASCADE, related_name='links')
    label = models.CharField('عنوان کانال یا شبکه', max_length=100)
    url = models.URLField('نشانی پیوند', validators=[web_link])
    position = models.PositiveIntegerField('ترتیب نمایش', default=0)

    class Meta:
        ordering = ('position', 'pk')
        verbose_name = 'پیوند شبکه یا کانال'
        verbose_name_plural = 'کانال‌ها و شبکه‌های بیشتر'

    def __str__(self):
        return self.label
