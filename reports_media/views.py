from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from dorm_heiat.unit_filter import unit_filter

from .assets import format_for
from .forms import ArchiveFilters
from .models import MediaFile, MediaPost

ORDER = {
    'newest': ('-published_at', '-pk'),
    'event': ('-event_date', '-published_at', '-pk'),
    'popular': ('-views', '-published_at', '-pk'),
}


@require_safe
@never_cache
def archive(request):
    form = ArchiveFilters(request.GET or None)
    scope = unit_filter(request)
    posts = scope.apply(MediaPost.objects.visible(archived=True)).select_related('category').prefetch_related(
        'events', 'units__parent', 'units__unit_type'
    )
    sort = 'newest'
    if form.is_bound:
        if form.is_valid():
            data = form.cleaned_data
            if term := data['q']:
                posts = posts.filter(Q(title__icontains=term) | Q(summary__icontains=term)
                                     | Q(description__icontains=term) | Q(tags__name__icontains=term))
            for field, lookup in (
                ('date_from', 'event_date__gte'), ('date_to', 'event_date__lte'), ('kind', 'kind'),
                ('category', 'category'), ('event', 'events'),
            ):
                if data[field]:
                    posts = posts.filter(**{lookup: data[field]})
            sort = data['sort'] or sort
        else:
            posts = posts.none()
    page = Paginator(posts.distinct().order_by(*ORDER[sort]), 12).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'reports_media/archive.html', {
        'form': form, 'page': page, 'params': params.urlencode(), 'scope': scope,
    })


@require_safe
@never_cache
def detail(request, pk):
    visible = MediaPost.objects.visible(archived=True)
    post = get_object_or_404(visible.select_related('category').prefetch_related('events', 'units', 'tags'), pk=pk)
    if request.method == 'GET':
        visible.filter(pk=pk).update(views=F('views') + 1)
    items = []
    for attachment in post.attachments.filter(private=False):
        try:
            online = attachment.online
        except (ValidationError, ValueError):
            online = None
        if online:
            kind, url = online
        elif attachment.file:
            kind = format_for(attachment.file.name)[0]
            url = None
        else:
            continue
        items.append({'attachment': attachment, 'kind': kind, 'online_url': url})
    return render(request, 'reports_media/detail.html', {'post': post, 'items': items, 'scope': unit_filter(request)})


def admin_can_view(user, model):
    return user.is_active and user.is_staff and (
        user.has_perm(f'reports_media.view_{model}') or user.has_perm(f'reports_media.change_{model}')
    )


def serve_asset(request, field):
    if not field:
        raise Http404
    kind, mime, _ = format_for(field.name)
    try:
        stream = field.open('rb')
    except FileNotFoundError as error:
        raise Http404 from error
    response = FileResponse(stream, content_type=mime,
                            as_attachment='download' in request.GET or kind in {'document', 'download'})
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response


@require_safe
@never_cache
def cover(request, pk):
    posts = MediaPost.objects.all() if admin_can_view(request.user, 'mediapost') else MediaPost.objects.visible(archived=True)
    return serve_asset(request, get_object_or_404(posts, pk=pk).cover)


@require_safe
@never_cache
def attachment(request, pk):
    files = MediaFile.objects.all()
    if not (admin_can_view(request.user, 'mediapost') and admin_can_view(request.user, 'mediafile')):
        files = files.filter(private=False, post__in=MediaPost.objects.visible(archived=True))
    return serve_asset(request, get_object_or_404(files, pk=pk).file)
