from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from .unit_filter import unit_filter


@require_safe
def home(request):
    from announcements.models import Announcement
    from night_gatherings.models import Gathering, GatheringNotice, GatheringReport
    from night_gatherings.views import upcoming_filter
    from publications.models import Publication
    from registrations_campaigns.views import public_campaigns
    from reports_media.models import MediaPost

    scope = unit_filter(request)
    sections = [
        ('اطلاعیه‌ها', 'announcements:list', Announcement.visible()),
        ('گزارش‌ها و آرشیو رسانه', 'reports_media:archive',
         MediaPost.objects.visible().order_by('-published_at', '-pk')),
        ('نشریات', 'publications:list', Publication.visible()),
        ('پویش‌ها', 'registrations_campaigns:campaigns', public_campaigns()),
    ]
    gatherings = scope.apply(Gathering.visible())
    upcoming = gatherings.filter(upcoming_filter()).order_by('starts_at', 'pk').prefetch_related(
        Prefetch('notices', queryset=GatheringNotice.visible())
    )
    held = gatherings.exclude(upcoming_filter()).prefetch_related(Prefetch('reports', queryset=GatheringReport.visible()))
    return render(request, 'home.html', {
        'scope': scope,
        'upcoming_gatherings': upcoming[:3],
        'held_gatherings': held[:3],
        'sections': [(label, route, scope.apply(queryset)[:6]) for label, route, queryset in sections],
    })


@require_safe
def editorial_list(request, model, label):
    scope = unit_filter(request)
    page = Paginator(scope.apply(model.visible()), 12).get_page(request.GET.get('page'))
    return render(request, 'dorm_heiat/editorial_list.html', {'scope': scope, 'page': page, 'label': label})


@require_safe
def editorial_detail(request, pk, model, label):
    item = get_object_or_404(model.visible().prefetch_related('units__parent', 'units__unit_type'), pk=pk)
    return render(request, 'dorm_heiat/editorial_detail.html', {
        'item': item, 'label': label, 'scope': unit_filter(request),
    })
