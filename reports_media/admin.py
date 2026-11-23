from dataclasses import dataclass

from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

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
            value = ProtectedFileLink(
                value.name,
                reverse(f'reports_media:{route}', args=[instance.pk]),
            )
        return super().get_context(name, value, attrs)


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    fields = ('order', 'caption', 'file', 'embed', 'preview_player', 'private')
    readonly_fields = ('preview_player',)
    formfield_overrides = {
        models.FileField: {'widget': ProtectedFileWidget},
    }

    @admin.display(description='پیش‌نمایش در پنل')
    def preview_player(self, instance):
        if not instance or not instance.pk:
            return 'پس از ذخیره در دسترس است'

        if instance.embed:
            try:
                kind, url = instance.online
                if kind in ('frame', 'document_frame'):
                    return format_html(
                        '<iframe src="{}" width="200" height="115" '
                        'frameborder="0" allowfullscreen loading="lazy"></iframe>',
                        url,
                    )
            except Exception:
                return format_html(
                    '<span style="color:red;">پیوند نامعتبر است</span>'
                )

        if instance.file:
            file_url = reverse('reports_media:file', args=[instance.pk])
            ext = instance.file.name.lower()

            if ext.endswith(('.mp4', '.webm')):
                return format_html(
                    '<video src="{}" width="200" controls '
                    'preload="metadata"></video>',
                    file_url,
                )
            elif ext.endswith(('.mp3', '.wav', '.ogg')):
                return format_html(
                    '<audio src="{}" controls preload="metadata" '
                    'style="max-width:200px;"></audio>',
                    file_url,
                )
            elif ext.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return format_html(
                    '<img src="{}" style="max-height:80px; '
                    'border-radius:4px;" />',
                    file_url,
                )

        return '—'


@admin.register(MediaPost)
class MediaPostAdmin(UnitContentAdmin):
    list_display = (
        'title',
        'status',
        'kind',
        'category',
        'event_date',
        'published_at',
        'views',
    )
    list_filter = ('status', 'kind', 'category', 'events', 'units', 'is_public')
    search_fields = ('title', 'summary', 'description', 'tags__name')
    filter_horizontal = ('tags', 'events', 'units')
    inlines = [MediaFileInline]
    readonly_fields = ('created_by', 'views', 'cover_preview')
    formfield_overrides = {
        models.FileField: {'widget': ProtectedFileWidget},
    }

    fieldsets = (
        ('اطلاعات اصلی و عنوان', {
            'fields': ('title', 'kind', 'category', 'responsible'),
        }),
        ('متن و محتوای گزارش', {
            'fields': ('summary', 'description'),
            'description': (
                'متن کامل گزارش را با استفاده از ویرایشگر پیشرفته '
                'با قابلیت‌های تیتر، جدول، نقل‌قول و پیوند تکمیل کنید.'
            ),
        }),
        ('تصویر شاخص و رسانه', {
            'fields': ('cover', 'cover_preview'),
        }),
        ('دسته‌بندی‌ها و رویدادها', {
            'fields': (
                'event_date',
                'events',
                'tags',
                'units',
                'is_public',
            ),
            'classes': ('collapse',),
        }),
        ('تنظیمات انتشار و بایگانی', {
            'fields': (
                'status',
                'published_at',
                'show_in_archive',
                'created_by',
                'views',
            ),
        }),
    )

    class Media:
        css = {
            'all': [
                'django_ckeditor_5/dist/styles.css',
            ],
        }
        js = [
            'django_ckeditor_5/dist/bundle.js',
        ]

    @admin.display(description='پیش‌نمایش تصویر شاخص')
    def cover_preview(self, obj):
        # در صفحه افزودن، یا پیش از ذخیره، obj.pk هنوز وجود ندارد.
        if not obj or not obj.pk or not obj.cover:
            return '—'

        url = reverse('reports_media:cover', args=[obj.pk])
        return format_html(
            '<img src="{}" style="max-height:120px; border-radius:6px;" />',
            url,
        )

    def can_publish(self, request):
        return request.user.has_perm('reports_media.publish_mediapost')

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if not self.can_publish(request):
            fields.append('show_in_archive')
        return fields

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status' and not self.can_publish(request):
            kwargs['choices'] = [
                (value, label)
                for value, label in MediaPost.Status.choices
                if value in (
                    MediaPost.Status.DRAFT,
                    MediaPost.Status.PENDING,
                )
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (
            obj is None
            or self.can_publish(request)
            or obj.status in (
                MediaPost.Status.DRAFT,
                MediaPost.Status.PENDING,
            )
        )

    def save_model(self, request, obj, form, change):
        if (
            not self.can_publish(request)
            and obj.status not in (
                MediaPost.Status.DRAFT,
                MediaPost.Status.PENDING,
            )
        ):
            raise PermissionDenied

        if not change:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)


@admin.register(Category, Tag, Event)
class TaxonomyAdmin(admin.ModelAdmin):
    search_fields = ('name',)
