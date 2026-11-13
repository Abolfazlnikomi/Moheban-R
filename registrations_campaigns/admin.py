from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from dorm_heiat.admin import UnitContentAdmin

from .exports import campaign_export, volunteer_export
from .models import Campaign, CampaignEntry, CampaignField, VolunteerApplication, VolunteerSection, VolunteerSettings


@admin.register(VolunteerSettings)
class VolunteerSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return super().has_add_permission(request) and not VolunteerSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VolunteerSection)
class VolunteerSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'section', 'status', 'created_at')
    list_filter = ('status', 'section', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'national_id', 'skills')
    readonly_fields = ('first_name', 'last_name', 'phone', 'national_id', 'birth_date', 'skills',
                       'section', 'availability', 'created_at')
    actions = ('export_excel',)

    def has_add_permission(self, request):
        return False

    def has_export_permission(self, request):
        return self.has_view_or_change_permission(request) and request.user.has_perm(
            'registrations_campaigns.export_volunteerapplication'
        )

    @admin.action(permissions=['export'], description='خروجی Excel درخواست‌های انتخاب‌شده')
    def export_excel(self, request, queryset):
        return volunteer_export(queryset)


class CampaignFieldInline(admin.TabularInline):
    model = CampaignField
    extra = 0


@admin.register(Campaign)
class CampaignAdmin(UnitContentAdmin):
    list_display = ('title', 'status', 'starts_on', 'ends_on', 'participation')
    list_filter = ('status', 'participation', 'starts_on', 'ends_on', 'units', 'is_public')
    search_fields = ('title', 'description')
    inlines = (CampaignFieldInline,)

    def can_export(self, request):
        user = request.user
        return user.has_perm('registrations_campaigns.export_campaignentry') and (
            user.has_perm('registrations_campaigns.view_campaignentry')
            or user.has_perm('registrations_campaigns.change_campaignentry')
        )

    def get_readonly_fields(self, request, obj=None):
        return ('excel_link',) if obj and self.can_export(request) else ()

    @admin.display(description='خروجی مشارکت‌کنندگان')
    def excel_link(self, obj):
        url = reverse('admin:registrations_campaigns_campaign_export', args=[obj.pk], current_app=self.admin_site.name)
        return format_html('<a href="{}">دریافت Excel این پویش</a>', url)

    def get_urls(self):
        return [
            path('<int:object_id>/export/', self.admin_site.admin_view(self.export_view),
                 name='registrations_campaigns_campaign_export'),
        ] + super().get_urls()

    def export_view(self, request, object_id):
        if not self.has_view_or_change_permission(request) or not self.can_export(request):
            raise PermissionDenied
        campaign = self.get_object(request, object_id)
        if campaign is None:
            raise Http404
        if not self.has_view_or_change_permission(request, campaign):
            raise PermissionDenied
        return campaign_export(campaign)


@admin.register(CampaignEntry)
class CampaignEntryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'campaign', 'created_at')
    list_filter = ('campaign', 'created_at')
    search_fields = ('full_name', 'phone', 'campaign__title', 'answers')
    fields = readonly_fields = ('campaign', 'full_name', 'phone', 'created_at', 'display_answers')

    def has_add_permission(self, request):
        return False

    @admin.display(description='پاسخ‌ها')
    def display_answers(self, obj):
        return format_html_join(
            '', '<p><strong>{}:</strong> {}</p>',
            ((answer['label'], answer['value']) for answer in obj.answers),
        )
