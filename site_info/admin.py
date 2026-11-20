from django.contrib import admin

from .models import FooterSettings, SocialLink


class SocialLinkInline(admin.TabularInline):
    model = SocialLink
    extra = 1


@admin.register(FooterSettings)
class FooterSettingsAdmin(admin.ModelAdmin):
    inlines = (SocialLinkInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
