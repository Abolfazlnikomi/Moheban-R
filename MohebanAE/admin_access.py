from copy import copy

from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.apps import apps
from django.core.exceptions import ValidationError
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .admin_roles import FULL_ADMIN_GROUP, is_full_admin


PERMISSION_ACTIONS = {
    'add': 'افزودن',
    'change': 'ویرایش',
    'delete': 'حذف',
    'view': 'مشاهده',
    'publish': 'انتشار',
    'export': 'دریافت خروجی',
}


def permission_label(permission):
    content_type = permission.content_type
    model = content_type.model_class()
    action, _, model_name = permission.codename.partition('_')
    if model is None or action not in PERMISSION_ACTIONS or model_name != content_type.model:
        return str(permission)
    app_label = apps.get_app_config(content_type.app_label).verbose_name
    return f'{app_label} | {PERMISSION_ACTIONS[action]} {model._meta.verbose_name}'


class SiteAdminLoginForm(AdminAuthenticationForm):
    def get_admin_site(self):
        return admin.site

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        candidate = copy(self.request)
        candidate.user = user
        if not self.get_admin_site().has_permission(candidate):
            raise ValidationError(self.error_messages['invalid_login'], code='invalid_login',
                                  params={'username': self.username_field.verbose_name})


class SiteAdmin(admin.AdminSite):
    login_form = SiteAdminLoginForm
    site_header = 'پنل مدیر کل محبان'
    site_title = 'پنل مدیر کل'

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser


class StaffPanelLoginForm(SiteAdminLoginForm):
    def get_admin_site(self):
        return staff_panel


class StaffPanel(admin.AdminSite):
    login_form = StaffPanelLoginForm
    site_header = 'پنل ادمین و کاربران مجاز محبان'
    site_title = 'پنل ادمین'
    index_title = 'بخش‌های در دسترس شما'

    def admin_view(self, view, cacheable=False):
        return xframe_options_sameorigin(super().admin_view(view, cacheable))

    def has_permission(self, request):
        return super().has_permission(request) and (
            request.user.is_superuser or any(
                any(model_admin.get_model_perms(request).values())
                for model_admin in self._registry.values()
            )
        )


staff_panel = StaffPanel(name='staff_panel')


class ManageAccounts:
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if field is not None and db_field.name in ('permissions', 'user_permissions'):
            field.queryset = field.queryset.select_related('content_type')
            field.label_from_instance = permission_label
        return field

    def can_manage(self, request):
        return request.user.is_superuser or is_full_admin(request.user)

    def has_module_permission(self, request):
        return self.can_manage(request) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self.can_manage(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self.can_manage(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.can_manage(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.can_manage(request) and super().has_delete_permission(request, obj)


class ProtectPrivilegedUsers:
    def get_queryset(self, request):
        users = super().get_queryset(request)
        if not request.user.is_superuser:
            users = users.filter(is_superuser=False).exclude(groups__name=FULL_ADMIN_GROUP)
        return users

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields if request.user.is_superuser else (*fields, 'is_superuser')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'groups' and not request.user.is_superuser:
            kwargs['queryset'] = db_field.remote_field.model.objects.exclude(name=FULL_ADMIN_GROUP)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class ProtectFullAdminGroup:
    def get_queryset(self, request):
        groups = super().get_queryset(request)
        return groups if request.user.is_superuser else groups.exclude(name=FULL_ADMIN_GROUP)

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return (*fields, 'name') if obj and obj.name == FULL_ADMIN_GROUP else fields

    def has_delete_permission(self, request, obj=None):
        return (obj is None or obj.name != FULL_ADMIN_GROUP) and super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset.exclude(name=FULL_ADMIN_GROUP))
