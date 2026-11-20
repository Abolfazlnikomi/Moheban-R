from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from dorm_heiat.unit_filter import unit_filter
from night_gatherings.models import Gathering
from reports_media.views import serve_asset

from .models import Announcement, AnnouncementImage


@require_safe
def listing(request, archived=False):
    scope = unit_filter(request)
    entries = scope.apply(Announcement.visible())
    page = Paginator(entries if archived else entries[:12], 12).get_page(request.GET.get('page'))
    return render(request, 'announcements/list.html', {'scope': scope, 'page': page, 'archived': archived})


@require_safe
def detail(request, pk):
    item = get_object_or_404(
        Announcement.visible().prefetch_related('images', 'units__parent', 'units__unit_type'), pk=pk,
    )
    gathering = Gathering.visible().filter(pk=item.gathering_id).first() if item.gathering_id else None
    return render(request, 'announcements/detail.html', {
        'item': item, 'gathering': gathering, 'scope': unit_filter(request),
    })


@never_cache
@require_safe
def image(request, pk):
    images = AnnouncementImage.objects.all()
    user = request.user
    if not (user.is_active and user.is_staff and (
        user.has_perm('announcements.view_announcement') or user.has_perm('announcements.change_announcement')
    )):
        images = images.filter(announcement__in=Announcement.visible())
    return serve_asset(request, get_object_or_404(images, pk=pk).file)
