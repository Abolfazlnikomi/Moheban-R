from django.db.models import Prefetch
from django.shortcuts import render
from django.views.decorators.http import require_safe

from dorm_heiat.unit_filter import unit_filter


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
    return render(request, 'home_page/index.html', {
        'scope': scope,
        'upcoming_gatherings': upcoming[:3],
        'held_gatherings': held[:3],
        'sections': [(label, route, scope.apply(queryset)[:6]) for label, route, queryset in sections],
    })
