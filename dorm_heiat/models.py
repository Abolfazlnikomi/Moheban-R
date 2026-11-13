from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class UnitType(models.Model):
    name = models.CharField('نام نوع', max_length=150, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'نوع واحد'
        verbose_name_plural = 'نوع‌های واحد'

    def __str__(self):
        return self.name


class Unit(models.Model):
    class Audience(models.TextChoices):
        COMMON = 'common', 'مشترک / بدون تفکیک'
        SISTERS = 'sisters', 'خواهران'
        BROTHERS = 'brothers', 'برادران'

    name = models.CharField('نام واحد', max_length=150)
    description = models.TextField('توضیحات', blank=True)
    unit_type = models.ForeignKey(UnitType, models.PROTECT, verbose_name='نوع واحد')
    parent = models.ForeignKey('self', models.PROTECT, null=True, blank=True, related_name='children',
                               verbose_name='واحد والد')
    audience = models.CharField('تفکیک', max_length=8, choices=Audience.choices, default=Audience.COMMON)
    active = models.BooleanField('فعال', default=True)

    class Meta:
        ordering = ('name', 'pk')
        verbose_name = 'واحد'
        verbose_name_plural = 'واحدها و زیرواحدها'

    def __str__(self):
        return f'{self.name} — {self.unit_type}' if self.parent_id is None else f'{self.parent.name} / {self.name}'

    def clean(self):
        super().clean()
        parents = dict(Unit.objects.values_list('pk', 'parent_id'))
        seen = {self.pk}
        current = self.parent_id
        while current is not None:
            if current in seen:
                raise ValidationError({'parent': 'یک واحد نمی‌تواند والد خودش یا یکی از نیاکانش باشد.'})
            seen.add(current)
            current = parents.get(current)


class UnitContent(models.Model):
    units = models.ManyToManyField(Unit, blank=True, verbose_name='واحدهای مرتبط')
    is_public = models.BooleanField('محتوای عمومی', default=True,
                                    help_text='محتوای عمومی می‌تواند بدون واحد منتشر شود. این گزینه مجوز دسترسی نیست.')

    class Meta:
        abstract = True


def discoverable(queryset):
    return queryset.filter(Q(is_public=True) | Q(units__isnull=False)).distinct()


class EditorialContent(UnitContent):
    title = models.CharField('عنوان', max_length=200)
    summary = models.TextField('خلاصه', max_length=600, blank=True)
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
        return discoverable(cls.objects.filter(published=True, published_at__lte=timezone.now()))
