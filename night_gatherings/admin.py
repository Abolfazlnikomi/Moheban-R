from dataclasses import dataclass

from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.urls import reverse

from dorm_heiat.admin import UnitContentAdmin, UnitContentForm

from .models import Gathering, GatheringNotice, GatheringReport, ReportAsset


@dataclass
class ProtectedFileLink:
    name: str
    url: str

    def __str__(self):
        return self.name


class ProtectedFileWidget(AdminFileWidget):
    def get_context(self, name, value, attrs):
        if value and getattr(value, 'instance', None) and value.instance.pk:
            routes = {Gathering: 'poster', GatheringNotice: 'notice_poster', ReportAsset: 'asset'}
            route = routes[type(value.instance)]
            value = ProtectedFileLink(value.name, reverse(f'night_gatherings:{route}', args=[value.instance.pk]))
        return super().get_context(name, value, attrs)


class PublicationPermissions:
    publication_field = 'published'

    def can_publish(self, request):
        return request.user.has_perm(f'night_gatherings.publish_{self.opts.model_name}')

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields if self.can_publish(request) else (*fields, self.publication_field)

    def is_publication_managed(self, obj):
        return bool(getattr(obj, self.publication_field))

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (
            obj is None or self.can_publish(request) or not self.is_publication_managed(obj)
        )


class GatheringForm(UnitContentForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'units' in self.fields:
            self.fields['units'].required = True


@admin.register(Gathering)
class GatheringAdmin(PublicationPermissions, UnitContentAdmin):
    form = GatheringForm
    publication_field = 'status'
    list_display = ('title', 'starts_at', 'venue', 'status')
    list_filter = ('status', 'units', 'starts_at')
    search_fields = ('title', 'venue', 'guests', 'units__name')
    formfield_overrides = {models.FileField: {'widget': ProtectedFileWidget}}

    def is_publication_managed(self, obj):
        return obj.status != Gathering.Status.DRAFT


class GatheringContentAdmin(PublicationPermissions, admin.ModelAdmin):
    list_display = ('title', 'gathering', 'published', 'published_at')
    list_filter = ('published', 'published_at')
    search_fields = ('title', 'gathering__title', 'description')
    autocomplete_fields = ('gathering',)


@admin.register(GatheringNotice)
class GatheringNoticeAdmin(GatheringContentAdmin):
    formfield_overrides = {models.FileField: {'widget': ProtectedFileWidget}}


class ReportAssetInline(admin.TabularInline):
    model = ReportAsset
    extra = 0
    formfield_overrides = {models.FileField: {'widget': ProtectedFileWidget}}


@admin.register(GatheringReport)
class GatheringReportAdmin(GatheringContentAdmin):
    inlines = (ReportAssetInline,)
