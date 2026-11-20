from django.contrib import admin

from dorm_heiat.admin import EditorialAdmin
from .forms import AnnouncementForm
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(EditorialAdmin):
    form = AnnouncementForm
    fields = (*AnnouncementForm.Meta.fields, 'new_images', 'remove_images')

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return fields if obj and obj.images.exists() else tuple(field for field in fields if field != 'remove_images')
