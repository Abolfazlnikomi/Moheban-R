from django import forms
from django.urls import reverse
from django.utils.html import format_html

from dorm_heiat.admin import UnitContentForm
from reports_media.assets import validate_cover

from .models import Announcement, AnnouncementImage


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data] if data else []
        clean_image = super().clean
        return [clean_image(file) for file in files]


class ExistingImagesField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, image):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('announcements:image', args=[image.pk]),
            image,
        )


class AnnouncementForm(UnitContentForm):
    new_images = MultipleImageField(
        label='تصاویر جدید',
        required=False,
        validators=[validate_cover],
        help_text='یک یا چند تصویر JPG، PNG یا WebP انتخاب کنید.',
    )
    remove_images = ExistingImagesField(
        label='تصاویر برای حذف',
        queryset=AnnouncementImage.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Announcement
        fields = (
            'title',
            'summary',
            'description',
            'cover',
            'published',
            'published_at',
            'expires_at',
            'is_public',
            'units',
            'gathering',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and 'remove_images' in self.fields:
            images = self.instance.images.all()
            if images.exists():
                self.fields['remove_images'].queryset = images
            else:
                self.fields.pop('remove_images')
        else:
            self.fields.pop('remove_images', None)

    def _save_m2m(self):
        super()._save_m2m()

        if 'remove_images' in self.cleaned_data:
            self.cleaned_data['remove_images'].delete()

        for file in self.cleaned_data.get('new_images', []):
            self.instance.images.create(file=file)
