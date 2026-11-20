from django.conf import settings
from django.db import models


class Scope(models.Model):
    name = models.CharField('نام حوزه', max_length=150, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'حوزهٔ تجربه‌نگاری'
        verbose_name_plural = 'حوزه‌های تجربه‌نگاری'

    def __str__(self):
        return self.name


class Subgroup(models.Model):
    scope = models.ForeignKey(Scope, models.PROTECT, related_name='subgroups', verbose_name='حوزه')
    name = models.CharField('نام زیرگروه', max_length=150)

    class Meta:
        ordering = ('scope__name', 'name')
        constraints = [models.UniqueConstraint(fields=('scope', 'name'), name='experience_unique_subgroup')]
        verbose_name = 'زیرگروه تجربه‌نگاری'
        verbose_name_plural = 'زیرگروه‌های تجربه‌نگاری'

    def __str__(self):
        return f'{self.scope} / {self.name}'


class ExperienceAccess(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, models.CASCADE, related_name='experience_access')
    enabled = models.BooleanField('دسترسی تجربه‌نگاری فعال باشد', default=False)
    scopes = models.ManyToManyField(Scope, blank=True, verbose_name='حوزه‌های مجاز')

    class Meta:
        verbose_name = 'دسترسی تجربه‌نگاری'
        verbose_name_plural = 'دسترسی تجربه‌نگاری'


class Experience(models.Model):
    subgroup = models.ForeignKey(Subgroup, models.PROTECT, related_name='experiences', verbose_name='زیرگروه')
    title = models.CharField('عنوان یا توضیح کوتاه', max_length=200)
    body = models.TextField('متن اصلی تجربه')
    recorded_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.SET_NULL, null=True, related_name='written_experiences', verbose_name='نویسنده',
    )

    class Meta:
        ordering = ('-recorded_at', '-pk')
        verbose_name = 'تجربه'
        verbose_name_plural = 'تجربه‌ها'

    def __str__(self):
        return self.title
