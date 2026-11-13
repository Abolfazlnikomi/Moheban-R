from django import forms
from django.contrib import admin
from django.db.models import Q

from .models import Unit, UnitType
from .unit_filter import UnitTree


@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'unit_type', 'audience', 'active')
    list_filter = ('active', 'unit_type', 'audience')
    search_fields = ('name', 'description', 'parent__name')
    autocomplete_fields = ('parent', 'unit_type')


class UnitContentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'units' in self.fields:
            active_ids = UnitTree().active_ids
            existing = self.instance.units.values('pk') if self.instance.pk else []
            self.fields['units'].queryset = Unit.objects.filter(
                Q(pk__in=active_ids) | Q(pk__in=existing)
            ).select_related('parent', 'unit_type')

    def clean(self):
        data = super().clean()
        if data.get('is_public') is False and 'units' in data and not data['units']:
            self.add_error('units', 'برای محتوای غیرعمومی دست‌کم یک واحد انتخاب کنید.')
        return data


class UnitContentAdmin(admin.ModelAdmin):
    form = UnitContentForm
    filter_horizontal = ('units',)


class EditorialAdmin(UnitContentAdmin):
    list_display = ('title', 'published', 'is_public', 'published_at')
    list_filter = ('published', 'is_public', 'units')
    search_fields = ('title', 'summary', 'description')
    date_hierarchy = 'published_at'
