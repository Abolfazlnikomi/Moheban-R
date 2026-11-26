from functools import wraps

from django import forms
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models, router, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from feedback_polls.forms import ModerationFilter
from feedback_polls.models import Feedback
from night_gatherings.models import Gathering, GatheringNotice, ReportAsset
from registrations_campaigns.exports import campaign_export, volunteer_export
from registrations_campaigns.models import Campaign, CampaignEntry, VolunteerApplication, VolunteerSettings
from reports_media.models import MediaFile, MediaPost

from MohebanAE.admin_access import permission_label
from MohebanAE.admin_roles import FULL_ADMIN_GROUP
from .registry import BY_MODEL, MODULES, RESOURCES, workspace_navigation


FILE_ROUTES = {
    (MediaPost, 'cover'): 'reports_media:cover',
    (MediaFile, 'file'): 'reports_media:file',
    (Gathering, 'poster'): 'night_gatherings:poster',
    (GatheringNotice, 'poster'): 'night_gatherings:notice_poster',
    (ReportAsset, 'file'): 'night_gatherings:asset',
    (Campaign, 'banner'): 'registrations_campaigns:campaign_banner',
}


def workspace_access(view):
    @never_cache
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def require_access(allowed):
    if not allowed:
        raise PermissionDenied


def get_parent(request, resource, parent_pk, *, editing=False):
    if resource.parent is None:
        return None
    parent_resource = BY_MODEL[resource.parent]
    queryset = parent_resource.queryset(request)
    if editing and request.method == 'POST':
        queryset = queryset.select_for_update()
    parent = get_object_or_404(queryset, pk=parent_pk)
    require_access(parent_resource.allows(request, 'change' if editing else 'view', parent))
    return parent


def list_or_index(request, resource, parent):
    if resource.allows(request, 'view'):
        return redirect(resource.url('changelist', parent=parent))
    if parent is not None:
        parent_resource = BY_MODEL[resource.parent]
        if parent_resource.allows(request, 'view', parent):
            return redirect(parent_resource.url('detail', obj=parent))
    return redirect('account')


def subsection_links(request, section, obj):
    if obj is None:
        return []
    can_view = section.allows(request, 'view', obj)
    can_edit = section.allows(request, 'change', obj)
    links = []
    for child in RESOURCES:
        if child.parent is not section.model:
            continue
        if can_view and child.allows(request, 'view'):
            links.append({'name': child.title, 'url': child.url('changelist', parent=obj),
                          'action': 'مشاهدهٔ فهرست', 'icon': 'layers'})
        if can_edit and child.allows(request, 'add'):
            links.append({'name': f'افزودن {child.model._meta.verbose_name}', 'url': child.url('add', parent=obj),
                          'action': 'ایجاد مورد جدید', 'icon': 'plus'})
    return links


def context_for(request, resource, parent, obj=None):
    section = BY_MODEL[resource.parent] if parent is not None else resource
    parent_url = section.url('detail', obj=parent) if parent is not None and section.allows(request, 'view', parent) else ''
    list_url = resource.url('changelist', parent=parent) if resource.allows(request, 'view') else ''
    detail_url = resource.url('detail', obj=obj, parent=parent) if obj is not None and resource.allows(
        request, 'view', obj
    ) else ''
    subsection_parent = parent if parent is not None else obj
    return {
        **workspace_navigation(request, resource),
        'resource': resource, 'parent': parent, 'parent_url': parent_url, 'list_url': list_url,
        'subsection_parent': subsection_parent,
        'subsection_links': subsection_links(request, section, subsection_parent),
        'cancel_url': detail_url or list_url or parent_url or reverse('account'),
    }


def display_field(obj, name):
    field = obj._meta.get_field(name)
    value = getattr(obj, name)
    data = {'label': field.verbose_name, 'value': value}
    if name == 'answers' and isinstance(obj, CampaignEntry):
        data.update(answers=value, value=None)
    elif isinstance(field, models.FileField):
        route = FILE_ROUTES.get((type(obj), name))
        data.update(value=value.name.rsplit('/', 1)[-1] if value else None,
                    url=reverse(route, args=[obj.pk]) if value and route else '')
    elif field.choices:
        data['value'] = getattr(obj, f'get_{name}_display')()
    elif field.many_to_many:
        values = value.all()
        if name in ('permissions', 'user_permissions'):
            data['value'] = '، '.join(permission_label(item) for item in values.select_related('content_type'))
        else:
            data['value'] = '، '.join(map(str, values))
    elif isinstance(value, bool):
        data['value'] = 'بله' if value else 'خیر'
    return data


class WorkspaceFileInput(forms.ClearableFileInput):
    template_name = 'django/forms/widgets/file.html'

    def is_initial(self, value):
        return bool(value)

    def render(self, name, value, attrs=None, renderer=None):
        upload = super().render(name, None, attrs, renderer)
        if not self.is_initial(value):
            return upload
        clear = ''
        if not self.is_required and not (attrs or {}).get('disabled'):
            clear = format_html(
                '<label><input type="checkbox" name="{}"{}> حذف فایل فعلی</label>',
                self.clear_checkbox_name(name), ' checked' if self.checked else '',
            )
        return format_html(
            '<span class="workspace-file-name">فایل فعلی: {}</span>{}{}',
            value.name.rsplit('/', 1)[-1], clear, upload,
        )


def build_form(request, resource, obj, parent):
    policy = resource.policy
    readonly = set(policy.get_readonly_fields(request, obj) if policy is not None else ())
    fields = [name for name in resource.fields
              if name not in readonly and resource.model._meta.get_field(name).editable]
    if resource.model is User and obj is None:
        base = UserCreationForm
    else:
        base = resource.form or forms.ModelForm

    def formfield(field, **kwargs):
        if field.choices and policy is not None:
            return policy.formfield_for_choice_field(field, request, **kwargs)
        if isinstance(field, models.FileField):
            kwargs['widget'] = WorkspaceFileInput
        return field.formfield(**kwargs)

    form_class = forms.modelform_factory(resource.model, form=base, fields=fields, formfield_callback=formfield)
    bound = request.method == 'POST'
    form = form_class(request.POST if bound else None, request.FILES if bound else None, instance=obj)
    for field in form.fields.values():
        if isinstance(field, forms.DateTimeField):
            field.widget = forms.DateTimeInput(format='%Y-%m-%dT%H:%M:%S', attrs={'type': 'datetime-local', 'step': 1})
        elif isinstance(field, forms.DateField):
            field.widget = forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
    if resource.model is User and 'groups' in form.fields and not request.user.is_superuser:
        form.fields['groups'].queryset = Group.objects.exclude(name=FULL_ADMIN_GROUP)
    for name in ('permissions', 'user_permissions'):
        if name in form.fields:
            form.fields[name].queryset = form.fields[name].queryset.select_related('content_type')
            form.fields[name].label_from_instance = permission_label
    if parent is not None:
        setattr(form.instance, resource.parent_field, parent)
    return form


@workspace_access
@require_safe
def section(request, section_key):
    if section_key not in MODULES:
        raise Http404
    context = workspace_navigation(request)
    active_module = next((module for module in context['management_modules'] if module['key'] == section_key), None)
    require_access(active_module is not None)
    return render(request, 'workspace/section.html', {**context, 'active_module': active_module})


@workspace_access
@require_safe
def resource_list(request, resource, parent_pk=None):
    parent = get_parent(request, resource, parent_pk)
    require_access(resource.allows(request, 'view'))
    entries = resource.filtered(request, parent)
    filters = ModerationFilter(request.GET) if resource.model is Feedback else None
    if filters is not None:
        entries = filters.apply(entries).select_related('category')
    page = Paginator(entries, 25).get_page(request.GET.get('page'))
    return render(request, 'workspace/list.html', {
        **context_for(request, resource, parent), 'page': page, 'query': request.GET.get('q', '')[:120],
        'search_filters': filters,
        'columns': [resource.model._meta.get_field(name).verbose_name for name in resource.columns],
        'rows': [{
            'object': obj, 'cells': [display_field(obj, name)['value'] for name in resource.columns],
            'url': resource.url('detail', obj=obj, parent=parent),
        } for obj in page.object_list if resource.allows(request, 'view', obj)],
        'add_url': resource.url('add', parent=parent) if resource.allows(request, 'add') and (
            parent is None or BY_MODEL[resource.parent].allows(request, 'change', parent)
        ) else '',
        'export_url': resource.url('export') if resource.model is VolunteerApplication
        and resource.policy.has_export_permission(request) else '',
    })


@workspace_access
@require_safe
def resource_detail(request, resource, pk, parent_pk=None):
    parent = get_parent(request, resource, parent_pk)
    obj = get_object_or_404(resource.queryset(request, parent), pk=pk)
    require_access(resource.allows(request, 'view', obj))
    parent_editable = parent is None or BY_MODEL[resource.parent].allows(request, 'change', parent)
    can_edit = parent_editable and resource.allows(request, 'change', obj)
    can_delete = parent_editable and resource.allows(request, 'delete', obj)
    return render(request, 'workspace/detail.html', {
        **context_for(request, resource, parent, obj), 'object': obj,
        'fields': [display_field(obj, field) for field in resource.fields],
        'change_url': resource.url('change', obj=obj, parent=parent) if can_edit and resource.model is not CampaignEntry else '',
        'delete_url': resource.url('delete', obj=obj, parent=parent) if can_delete else '',
        'password_url': resource.url('password_change', obj=obj) if resource.model is User and can_edit else '',
        'export_url': resource.url('export', obj=obj) if resource.model is Campaign and resource.policy.can_export(request) else '',
    })


@workspace_access
@require_http_methods(['GET', 'HEAD', 'POST'])
@transaction.atomic
def resource_form(request, resource, pk=None, parent_pk=None):
    parent = get_parent(request, resource, parent_pk, editing=True)
    obj = None
    if pk is None:
        require_access(resource.allows(request, 'add'))
    else:
        queryset = resource.queryset(request, parent)
        if request.method == 'POST':
            queryset = queryset.select_for_update()
        obj = get_object_or_404(queryset, pk=pk)
        require_access(resource.allows(request, 'change', obj))
        if resource.model is CampaignEntry:
            return redirect(resource.url('detail', obj=obj))
    form = build_form(request, resource, obj, parent)
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        if resource.model is VolunteerSettings and obj is None:
            instance.save(force_insert=True)
        elif resource.policy is not None:
            resource.policy.save_model(request, instance, form, change=obj is not None)
        else:
            instance.save()
        form.save_m2m()
        messages.success(request, 'تغییرات ذخیره شد.')
        if resource.allows(request, 'view', instance):
            return redirect(resource.url('detail', obj=instance, parent=parent))
        return list_or_index(request, resource, parent)
    return render(request, 'workspace/form.html', {
        **context_for(request, resource, parent, obj), 'object': obj, 'form': form, 'editing': pk is not None,
    })


@workspace_access
@require_http_methods(['GET', 'HEAD', 'POST'])
@transaction.atomic
def resource_delete(request, resource, pk, parent_pk=None):
    parent = get_parent(request, resource, parent_pk, editing=True)
    queryset = resource.queryset(request, parent)
    if request.method == 'POST':
        queryset = queryset.select_for_update()
    obj = get_object_or_404(queryset, pk=pk)
    require_access(resource.allows(request, 'delete', obj))
    collector = NestedObjects(using=router.db_for_write(type(obj), instance=obj))
    collector.collect([obj])
    blocked = bool(collector.protected) or obj == request.user
    for model, objects in collector.model_objs.items():
        if model in BY_MODEL and any(not BY_MODEL[model].allows(request, 'delete', item) for item in objects):
            blocked = True
    if request.method == 'POST' and not blocked:
        collector.delete()
        messages.success(request, 'مورد انتخابی حذف شد.')
        return list_or_index(request, resource, parent)
    return render(request, 'workspace/delete.html', {
        **context_for(request, resource, parent, obj), 'object': obj, 'blocked': blocked,
    }, status=403 if request.method == 'POST' and blocked else 200)


@workspace_access
@require_http_methods(['GET', 'HEAD', 'POST'])
@transaction.atomic
def user_password(request, pk):
    resource = BY_MODEL[User]
    queryset = resource.queryset(request)
    if request.method == 'POST':
        queryset = queryset.select_for_update()
    obj = get_object_or_404(queryset, pk=pk)
    require_access(resource.allows(request, 'change', obj))
    form = SetPasswordForm(obj, request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if obj == request.user:
            update_session_auth_hash(request, obj)
        messages.success(request, 'رمز عبور تغییر کرد.')
        return redirect(resource.url('detail', obj=obj))
    return render(request, 'workspace/form.html', {
        **context_for(request, resource, None, obj), 'object': obj, 'form': form, 'editing': True,
        'heading': 'تنظیم رمز عبور',
    })


@workspace_access
@require_safe
def export_campaign(request, pk):
    resource = BY_MODEL[Campaign]
    campaign = get_object_or_404(resource.queryset(request), pk=pk)
    require_access(resource.allows(request, 'view', campaign) and resource.policy.can_export(request))
    return campaign_export(campaign)


@workspace_access
@require_http_methods(['POST'])
def export_volunteers(request):
    resource = BY_MODEL[VolunteerApplication]
    require_access(resource.policy.has_export_permission(request))
    selected = [int(value) for value in request.POST.getlist('selected')[:25]
                if value.isascii() and value.isdigit() and len(value) <= 18]
    if not selected:
        messages.error(request, 'برای دریافت خروجی دست‌کم یک درخواست را انتخاب کنید.')
        return redirect(resource.url('changelist'))
    return volunteer_export(resource.queryset(request).filter(pk__in=selected))
