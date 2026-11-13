from dataclasses import dataclass

from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse

from dorm_heiat.admin import UnitContentAdmin

from .models import Category, Event, MediaFile, MediaPost, Tag


@dataclass
class ProtectedFileLink:
    name: str
    url: str

    def __str__(self):
        return self.name


class ProtectedFileWidget(AdminFileWidget):
    def get_context(self, name, value, attrs):
        if value and getattr(value, 'instance', None) and value.instance.pk:
            instance = value.instance
            route = 'file' if isinstance(instance, MediaFile) else 'cover'
            value = ProtectedFileLink(value.name, reverse(f'reports_media:{route}', args=[instance.pk]))
        return super().get_context(name, value, attrs)


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    formfield_overrides = {models.FileField: {'widget': ProtectedFileWidget}}


@admin.register(MediaPost)
class MediaPostAdmin(UnitContentAdmin):
    list_display = ('title', 'status', 'kind', 'category', 'event_date', 'published_at', 'views')
    list_filter = ('status', 'kind', 'category', 'events', 'units', 'is_public')
    search_fields = ('title', 'summary', 'description', 'tags__name')
    filter_horizontal = ('tags', 'events', 'units')
    inlines = [MediaFileInline]
    readonly_fields = ('created_by', 'views')
    formfield_overrides = {models.FileField: {'widget': ProtectedFileWidget}}

    def can_publish(self, request):
        return request.user.has_perm('reports_media.publish_mediapost')

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if self.can_publish(request) else (*self.readonly_fields, 'show_in_archive')

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status' and not self.can_publish(request):
            kwargs['choices'] = [(value, label) for value, label in MediaPost.Status.choices
                                 if value in (MediaPost.Status.DRAFT, MediaPost.Status.PENDING)]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (
            obj is None or self.can_publish(request)
            or obj.status in (MediaPost.Status.DRAFT, MediaPost.Status.PENDING)
        )

    def save_model(self, request, obj, form, change):
        if not self.can_publish(request) and obj.status not in (MediaPost.Status.DRAFT, MediaPost.Status.PENDING):
            raise PermissionDenied
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Category, Tag, Event)
class TaxonomyAdmin(admin.ModelAdmin):
    search_fields = ('name',)
