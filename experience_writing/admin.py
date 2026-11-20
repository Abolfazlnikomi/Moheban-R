from django.contrib import admin

from .models import ExperienceAccess, Scope, Subgroup


class ExperienceAccessInline(admin.StackedInline):
    model = ExperienceAccess
    fields = ('enabled', 'scopes')
    filter_horizontal = ('scopes',)
    extra = 1
    max_num = 1


class SubgroupInline(admin.TabularInline):
    model = Subgroup
    extra = 1


@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    inlines = (SubgroupInline,)
    search_fields = ('name',)
