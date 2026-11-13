from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from dorm_heiat.unit_filter import unit_filter
from reports_media.assets import format_for, resolve_embed
from reports_media.views import serve_asset

from .models import Gathering, GatheringNotice, GatheringReport, ReportAsset


def upcoming_filter():
    return Q(status=Gathering.Status.PUBLISHED, starts_at__gte=timezone.now())


@require_safe
@never_cache
def listing(request):
    scope = unit_filter(request)
    archived = request.GET.get('show') == 'archive'
    entries = scope.apply(Gathering.visible())
    if archived:
        entries = entries.exclude(upcoming_filter()).prefetch_related(
            Prefetch('reports', queryset=GatheringReport.visible())
        )
    else:
        entries = entries.filter(upcoming_filter()).order_by('starts_at', 'pk').prefetch_related(
            Prefetch('notices', queryset=GatheringNotice.visible())
        )
    entries = entries.prefetch_related('units__parent', 'units__unit_type')
    return render(request, 'night_gatherings/list.html', {
        'scope': scope, 'archived': archived, 'page': Paginator(entries, 12).get_page(request.GET.get('page')),
    })


def report_item(attachment):
    local_url = reverse('night_gatherings:asset', args=[attachment.pk]) if attachment.file else ''
    if attachment.embed:
        try:
            kind, url = resolve_embed(attachment.embed)
        except (ValidationError, ValueError):
            pass
        else:
            return {'attachment': attachment, 'kind': kind, 'online_url': url, 'source': url, 'local_url': local_url}
    if local_url:
        kind = format_for(attachment.file.name)[0]
        return {'attachment': attachment, 'kind': kind, 'source': local_url, 'local_url': local_url}
    return None


@require_safe
@never_cache
def detail(request, pk):
    gathering = get_object_or_404(Gathering.visible().prefetch_related('units__parent', 'units__unit_type'), pk=pk)
    notices = GatheringNotice.visible().filter(gathering=gathering)
    reports = GatheringReport.visible().filter(gathering=gathering).prefetch_related('assets')
    report_list = [
        (report, [item for attachment in report.assets.all() if (item := report_item(attachment))])
        for report in reports
    ]
    return render(request, 'night_gatherings/detail.html', {
        'gathering': gathering, 'notices': notices, 'report_list': report_list, 'scope': unit_filter(request),
    })


def can_view(user, model):
    name = model._meta.model_name
    return user.is_active and user.is_staff and (
        user.has_perm(f'night_gatherings.view_{name}') or user.has_perm(f'night_gatherings.change_{name}')
    )


@require_safe
@never_cache
def poster(request, pk):
    queryset = Gathering.objects.all() if can_view(request.user, Gathering) else Gathering.visible()
    return serve_asset(request, get_object_or_404(queryset, pk=pk).poster)


@require_safe
@never_cache
def notice_poster(request, pk):
    queryset = GatheringNotice.objects.all() if can_view(request.user, GatheringNotice) else GatheringNotice.visible()
    return serve_asset(request, get_object_or_404(queryset, pk=pk).poster)


@require_safe
@never_cache
def asset(request, pk):
    queryset = ReportAsset.objects.all()
    if not (can_view(request.user, GatheringReport) and can_view(request.user, ReportAsset)):
        queryset = queryset.filter(report__in=GatheringReport.visible())
    return serve_asset(request, get_object_or_404(queryset, pk=pk).file)
