from django.contrib import admin
from django.utils.html import format_html

from dorm_heiat.admin import EditorialAdmin

from .forms import AnnouncementForm
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(EditorialAdmin):
    form = AnnouncementForm

    fields = (
        *AnnouncementForm.Meta.fields,
        'new_images',
        'remove_images',
    )

    list_display = (
        'title',
        'published',
        'published_at',
        'expires_at',
        'has_cover',
    )
    list_filter = (
        'published',
        'is_public',
    )
    search_fields = (
        'title',
        'summary',
        'description',
    )
    date_hierarchy = 'published_at'

    @admin.display(description='عکس شاخص', boolean=True)
    def has_cover(self, obj):
        return bool(obj.cover)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        # در ایجاد اطلاعیه یا زمانی که هیچ عکسی ثبت نشده،
        # گزینهٔ «تصاویر برای حذف» نمایش داده نشود.
        if not obj or not obj.images.exists():
            return tuple(
                field for field in fields
                if field != 'remove_images'
            )

        return fields
