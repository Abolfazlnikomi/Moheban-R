from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from dorm_heiat.unit_filter import unit_filter
from night_gatherings.models import Gathering
from reports_media.views import serve_asset

from .models import Announcement, AnnouncementImage


def _public_announcements(now):
    # visible() همچنان منطق پایهٔ انتشار پروژه را اعمال می‌کند.
    # شرط زمانی را صریح نگه می‌داریم تا انتشار آینده زودتر نمایش داده نشود.
    return Announcement.visible().filter(
        published=True,
        published_at__lte=now,
    )


def _can_preview(request):
    user = request.user
    return (
        user.is_active
        and user.is_staff
        and (
            user.has_perm('announcements.view_announcement')
            or user.has_perm('announcements.change_announcement')
        )
    )


@never_cache
@require_safe
def listing(request, archived=False):
    now = timezone.now()
    scope = unit_filter(request)

    entries = scope.apply(_public_announcements(now)).order_by(
        '-published_at', '-pk',
    )
    current = entries.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )

    recent_ids = list(current.values_list('pk', flat=True)[:12])

    if archived:
        # شامل اطلاعیه‌های منقضی‌شده و اطلاعیه‌های قدیمی‌تر از ۱۲ مورد جاری.
        shown = entries.exclude(pk__in=recent_ids)
    else:
        shown = current.filter(pk__in=recent_ids)

    page = Paginator(shown, 12).get_page(request.GET.get('page'))
    return render(request, 'announcements/list.html', {
        'scope': scope,
        'page': page,
        'archived': archived,
    })


@never_cache
@require_safe
def detail(request, pk):
    item = get_object_or_404(
        _public_announcements(timezone.now()).prefetch_related(
            'images', 'units__parent', 'units__unit_type',
        ),
        pk=pk,
    )
    gathering = (
        Gathering.visible().filter(pk=item.gathering_id).first()
        if item.gathering_id else None
    )
    return render(request, 'announcements/detail.html', {
        'item': item,
        'gathering': gathering,
        'scope': unit_filter(request),
    })


@never_cache
@require_safe
def image(request, pk):
    images = AnnouncementImage.objects.all()

    if not _can_preview(request):
        images = images.filter(
            announcement__in=_public_announcements(timezone.now())
        )

    image_obj = get_object_or_404(images, pk=pk)
    return serve_asset(request, image_obj.file)


@never_cache
@require_safe
def cover(request, pk):
    announcements = (
        Announcement.objects.all()
        if _can_preview(request)
        else _public_announcements(timezone.now())
    )
    item = get_object_or_404(announcements, pk=pk)

    if not item.cover:
        raise Http404('این اطلاعیه عکس شاخص ندارد.')

    return serve_asset(request, item.cover)
