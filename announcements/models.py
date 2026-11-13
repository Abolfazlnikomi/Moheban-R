from django.urls import reverse

from dorm_heiat.models import EditorialContent


class Announcement(EditorialContent):
    class Meta(EditorialContent.Meta):
        verbose_name = 'اطلاعیه'
        verbose_name_plural = 'اطلاعیه‌ها'

    def get_absolute_url(self):
        return reverse('announcements:detail', args=[self.pk])
