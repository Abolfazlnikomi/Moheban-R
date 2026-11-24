
from django.contrib import admin
from .models import LiveStream


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'is_active',
        'created_at',
        'updated_at',
    )

    list_filter = ('is_active',)

    search_fields = ('title', 'description')

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('اطلاعات لایو', {
            'fields': ('title', 'description', 'embed_url')
        }),
        ('وضعیت پخش', {
            'fields': ('is_active',)
        }),
        ('اطلاعات زمانی', {
            'fields': ('created_at', 'updated_at')
        }),
    )
