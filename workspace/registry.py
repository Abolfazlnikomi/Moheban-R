from dataclasses import dataclass

from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.urls import reverse
from live.models import LiveStream
from announcements.models import Announcement
from announcements.forms import AnnouncementForm
from dorm_heiat.admin import UnitContentForm
from dorm_heiat.models import Unit, UnitType
from experience_writing.access import experience_access
from feedback_polls.models import Feedback, FeedbackCategory, Poll, PollOption
from night_gatherings.admin import GatheringForm
from night_gatherings.models import Gathering, GatheringNotice, GatheringReport, ReportAsset
from publications.models import Publication
from registrations_campaigns.models import Campaign, CampaignEntry, CampaignField, VolunteerApplication, VolunteerSection, VolunteerSettings
from reports_media.models import Category, Event, MediaFile, MediaPost, Tag
from site_info.models import FooterSettings, SocialLink

from MohebanAE.admin_roles import is_full_admin


@dataclass(frozen=True)
class Resource:
    model: type
    fields: tuple
    columns: tuple = ()
    search: tuple = ()
    form: type | None = None
    parent: type | None = None
    parent_field: str = ''

    @property
    def key(self):
        return f'{self.model._meta.app_label}_{self.model._meta.model_name}'

    @property
    def title(self):
        return self.model._meta.verbose_name_plural

    @property
    def policy(self):
        return admin.site.get_model_admin(self.model) if self.parent is None else None

    def url(self, action, *, obj=None, parent=None):
        args = [parent.pk] if parent is not None else []
        if obj is not None:
            args.append(obj.pk)
        return reverse(f'staff_panel:{self.key}_{action}', args=args)

    def allows(self, request, action, obj=None):
        user = request.user
        if not (user.is_authenticated and user.is_active and user.is_staff):
            return False
        if self.policy is not None:
            method = getattr(self.policy, f'has_{action}_permission')
            return method(request) if action == 'add' else method(request, obj)
        opts = self.model._meta
        actions = ('view', 'change') if action == 'view' else (action,)
        return any(user.has_perm(f'{opts.app_label}.{verb}_{opts.model_name}') for verb in actions)

    def queryset(self, request, parent=None):
        if self.parent is not None:
            return self.model._default_manager.filter(**{self.parent_field: parent})
        return self.policy.get_queryset(request)

    def filtered(self, request, parent=None):
        queryset = self.queryset(request, parent)
        for term in request.GET.get('q', '').strip()[:120].split():
            if self.search:
                conditions = Q()
                for field in self.search:
                    conditions |= Q(**{f'{field}__icontains': term})
                queryset = queryset.filter(conditions)
        return queryset.order_by(*self.model._meta.ordering, 'pk')


EDITORIAL = ('title', 'summary', 'description', 'published', 'published_at', 'is_public', 'units')
EDITORIAL_COLUMNS = ('published', 'published_at')
RESOURCES = (
    Resource(Announcement, (*EDITORIAL, 'gathering'), EDITORIAL_COLUMNS, ('title', 'description'), AnnouncementForm),
    Resource(Publication, EDITORIAL, EDITORIAL_COLUMNS, ('title', 'description'), UnitContentForm),
    Resource(MediaPost, ('title', 'summary', 'description', 'event_date', 'published_at', 'category', 'tags',
                         'events', 'kind', 'status', 'show_in_archive', 'cover', 'responsible',
                         'is_public', 'units', 'created_by', 'views'), ('kind', 'status', 'event_date'),
             ('title', 'summary', 'description'), UnitContentForm),
    Resource(Category, ('name',), search=('name',)),
    Resource(Tag, ('name',), search=('name',)),
    Resource(Event, ('name',), search=('name',)),
    Resource(Gathering, ('title', 'description', 'starts_at', 'venue', 'guests', 'poster', 'status',
                         'is_public', 'units'), ('starts_at', 'venue', 'status'), ('title', 'venue'), GatheringForm),
    Resource(GatheringNotice, ('title', 'gathering', 'description', 'published', 'published_at',
                               'starts_at', 'venue', 'poster'), EDITORIAL_COLUMNS, ('title', 'gathering__title')),
    Resource(GatheringReport, ('title', 'gathering', 'summary', 'description', 'published', 'published_at'),
             EDITORIAL_COLUMNS, ('title', 'gathering__title')),
    Resource(Campaign, ('title', 'description', 'banner', 'starts_on', 'ends_on', 'status', 'participation',
                        'instructions', 'is_public', 'units'), ('status', 'starts_on', 'ends_on'),
             ('title', 'description'), UnitContentForm),
    Resource(CampaignEntry, ('campaign', 'full_name', 'phone', 'created_at', 'answers'),
             ('campaign', 'created_at'), ('full_name', 'phone', 'campaign__title')),
    Resource(VolunteerSettings, ('enabled', 'require_birth_date', 'require_skills', 'require_availability')),
    Resource(VolunteerSection, ('name', 'active'), ('active',), ('name',)),
    Resource(VolunteerApplication, ('first_name', 'last_name', 'phone', 'national_id', 'birth_date',
                                    'skills', 'section', 'availability', 'status', 'created_at'),
             ('section', 'status', 'created_at'), ('first_name', 'last_name', 'phone')),
    Resource(Unit, ('name', 'description', 'unit_type', 'parent', 'audience', 'active'),
             ('unit_type', 'audience', 'active'), ('name', 'description')),
    Resource(UnitType, ('name',), search=('name',)),
    Resource(User, ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff',
                    'is_superuser', 'groups', 'user_permissions'), ('email', 'is_active', 'is_staff'),
             ('username', 'first_name', 'last_name', 'email')),
    Resource(Group, ('name', 'permissions'), search=('name',)),
    Resource(Feedback, ('title', 'body', 'category', 'kind', 'status', 'author', 'created_at'),
             ('category', 'kind', 'status', 'created_at'), ('title', 'body', 'category__name')),
    Resource(FeedbackCategory, ('name', 'position'), ('position',), ('name',)),
    Resource(Poll, ('question', 'category', 'status', 'created_at'), ('category', 'status'), ('question',)),
    Resource(PollOption, ('text', 'position'), ('position',), parent=Poll, parent_field='poll'),
    Resource(FooterSettings, ('name', 'about', 'goals', 'activities', 'contact', 'phone', 'email', 'address',
                              'channel_url', 'instagram_url')),
    Resource(SocialLink, ('label', 'url', 'position'), ('position',), parent=FooterSettings, parent_field='footer'),
    Resource(MediaFile, ('file', 'embed', 'caption', 'order', 'private'), ('order', 'private'),
             parent=MediaPost, parent_field='post'),
    Resource(ReportAsset, ('file', 'embed', 'caption', 'order'), ('order',),
             parent=GatheringReport, parent_field='report'),
    Resource(CampaignField, ('label', 'kind', 'required', 'options', 'order'), ('kind', 'required', 'order'),
             parent=Campaign, parent_field='campaign'),
    Resource(
    LiveStream,
    fields=('title', 'description', 'embed_url', 'is_active'),
    columns=('title', 'is_active', 'updated_at'),
    search=('title', 'description'),
),
)
BY_MODEL = {resource.model: resource for resource in RESOURCES}
VOLUNTEER_MODELS = (VolunteerSettings, VolunteerSection, VolunteerApplication)
MODULES = {
    'announcements': ('اطلاعیه‌ها', 'bell'),
    'publications': ('نشریات', 'book'),
    'reports_media': ('گزارش‌ها و رسانه', 'media'),
    'night_gatherings': ('تجمعات شبانه', 'calendar'),
    'registrations_campaigns': ('پویش‌ها', 'flag'),
    'volunteers': ('ثبت‌نام خُدام', 'heart'),
    'dorm_heiat': ('واحدها', 'layers'),
    'auth': ('کاربران و دسترسی‌ها', 'lock'),
    'feedback_polls': ('نظرات و نظرسنجی', 'heart'),
    'site_info': ('فوتر سایت', 'layers'),
    'live': ('پخش زنده', 'radio'),
}


def module_key(resource):
    return 'volunteers' if resource.model in VOLUNTEER_MODELS else resource.model._meta.app_label


def workspace_modules(request):
    modules = {}
    for resource in RESOURCES:
        if resource.parent is not None:
            continue
        list_url = resource.url('changelist') if resource.allows(request, 'view') else ''
        add_url = resource.url('add') if resource.allows(request, 'add') else ''
        if not (list_url or add_url):
            continue
        group = module_key(resource)
        name, icon = MODULES[group]
        if group not in modules:
            modules[group] = {
                'key': group, 'name': name, 'icon': icon, 'models': [],
                'url': reverse('staff_panel:section', args=[group]),
            }
        module = modules[group]
        if resource.model is LiveStream:
            module['url'] = reverse('staff_panel:live_management')

            module['models'].append({
                'name': resource.title,
                'url': reverse('staff_panel:live_management'),
                'action': 'مدیریت پخش زنده',
                'icon': 'radio',
            })

        else:
            module['models'].append({
                'name': resource.title,
                'url': list_url or add_url,
                'action': 'مشاهدهٔ فهرست' if list_url else 'افزودن مورد جدید',
                'icon': 'grid' if list_url else 'plus',
            })
    return list(modules.values())


def workspace_navigation(request, resource=None):
    modules = workspace_modules(request)
    context = {'management_modules': modules, 'can_use_experiences': experience_access(request) is not None}
    if modules:
        user = request.user
        if user.is_superuser:
            context['management_level'] = 'مدیر کل'
        elif is_full_admin(user):
            context['management_level'] = 'مدیر کامل'
        else:
            context['management_level'] = 'کاربر دارای مجوز مدیریت'
    if resource is not None:
        root = BY_MODEL[resource.parent] if resource.parent is not None else resource
        context['active_module'] = next((module for module in modules if module['key'] == module_key(root)), None)
    return context
