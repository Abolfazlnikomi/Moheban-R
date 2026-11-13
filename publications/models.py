from django.urls import reverse

from dorm_heiat.models import EditorialContent


class Publication(EditorialContent):
    class Meta(EditorialContent.Meta):
        verbose_name = 'نشریه'
        verbose_name_plural = 'نشریات'

    def get_absolute_url(self):
        return reverse('publications:detail', args=[self.pk])
