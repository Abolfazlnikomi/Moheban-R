from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import Context, Template
from django.urls import reverse
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

# قالب مدرن، مینیمال و یکپارچه آرشیو
ARCHIVE_TEMPLATE_STRING = """
{% extends "base.html" %}

{% block content %}
<style>
:root {
  --rm-primary: #0e3b2f;
  --rm-primary-dark: #08241c;
  --rm-primary-light: #165b49;
  --rm-accent: #d97706;
  --rm-accent-hover: #b45309;
  --rm-bg-main: #f8fafc;
  --rm-surface: #ffffff;
  --rm-border: #e2e8f0;
  --rm-text-main: #0f172a;
  --rm-text-muted: #64748b;
  --rm-radius-sm: 10px;
  --rm-radius-md: 16px;
  --rm-radius-lg: 24px;
}

.reports-container {
  max-width: 1300px;
  margin: 0 auto;
  padding: 2rem 1.25rem 5rem;
  direction: rtl;
  font-family: inherit;
  color: var(--rm-text-main);
}

/* هدر اصلی */
.reports-hero {
  position: relative;
  background: radial-gradient(circle at top right, var(--rm-primary-light), var(--rm-primary-dark));
  color: #fff;
  border-radius: var(--rm-radius-lg);
  padding: 3.5rem 2rem;
  text-align: center;
  margin-bottom: 2.5rem;
  overflow: hidden;
  box-shadow: 0 20px 40px -15px rgba(14, 59, 47, 0.3);
}

.reports-hero::after {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(217, 119, 6, 0.15) 0%, transparent 70%);
  pointer-events: none;
}

.reports-hero h1 {
  font-size: 2.25rem;
  font-weight: 900;
  letter-spacing: -0.5px;
  margin: 0 0 0.75rem;
}

.reports-hero p {
  font-size: 1.05rem;
  color: #93c5fd;
  color: #d1fae5;
  margin: 0 auto;
  max-width: 600px;
  opacity: 0.95;
  line-height: 1.7;
}

/* پنل فیلترها */
.reports-filters {
  background: var(--rm-surface);
  border: 1px solid var(--rm-border);
  border-radius: var(--rm-radius-md);
  padding: 1.75rem;
  margin-bottom: 2.5rem;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04);
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.filter-field label {
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
}

.filter-input,
.filter-select {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border-radius: var(--rm-radius-sm);
  border: 1px solid var(--rm-border);
  background-color: #f8fafc;
  color: #1e293b;
  outline: none;
  font-size: 0.88rem;
  font-family: inherit;
  transition: all 0.2s ease;
}

.filter-input:focus,
.filter-select:focus {
  border-color: var(--rm-accent);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.15);
}

.filter-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid #f1f5f9;
}

.filter-count {
  font-size: 0.85rem;
  color: var(--rm-text-muted);
}

.filter-buttons {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-filter-submit {
  background: var(--rm-primary);
  color: #fff;
  padding: 0.65rem 1.75rem;
  border-radius: var(--rm-radius-sm);
  font-weight: 700;
  font-size: 0.9rem;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(14, 59, 47, 0.2);
}

.btn-filter-submit:hover {
  background: var(--rm-primary-light);
  transform: translateY(-1px);
}

.btn-filter-reset {
  color: #ef4444;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
}

.btn-filter-reset:hover {
  text-decoration: underline;
}

/* شبکه کارت‌ها */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
}

.report-card {
  background: var(--rm-surface);
  border-radius: var(--rm-radius-md);
  border: 1px solid var(--rm-border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.report-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.08);
  border-color: #cbd5e1;
}

.card-media {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  background: #0f172a;
  overflow: hidden;
}

.card-cover {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.report-card:hover .card-cover {
  transform: scale(1.05);
}

.card-kind-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.3rem 0.65rem;
  border-radius: 6px;
  z-index: 2;
}

.card-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.card-title {
  margin: 0 0 0.75rem;
  font-size: 1.15rem;
  font-weight: 800;
  line-height: 1.55;
}

.card-title a {
  color: var(--rm-text-main);
  text-decoration: none;
  transition: color 0.2s;
}

.card-title a:hover {
  color: var(--rm-accent);
}

.card-summary {
  color: var(--rm-text-muted);
  font-size: 0.88rem;
  line-height: 1.65;
  margin-bottom: 1.25rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-grow: 1;
}

.meta-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #f1f5f9;
  font-size: 0.78rem;
}

.meta-group {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.meta-chip {
  background: #f1f5f9;
  color: var(--rm-text-muted);
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-weight: 500;
}

.meta-chip.category {
  background: #ecfdf5;
  color: var(--rm-primary);
  font-weight: 700;
}

/* صفحه‌بندی */
.pagination-wrapper {
  margin-top: 4rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
}

.page-btn {
  padding: 0.6rem 1.25rem;
  background: var(--rm-surface);
  border: 1px solid var(--rm-border);
  border-radius: var(--rm-radius-sm);
  color: var(--rm-text-main);
  text-decoration: none;
  font-weight: 700;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.page-btn:hover {
  border-color: var(--rm-primary);
  color: var(--rm-primary);
  background: #f8fafc;
}

.page-info {
  font-size: 0.85rem;
  color: var(--rm-text-muted);
  font-weight: 600;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 5rem 1.5rem;
  background: var(--rm-surface);
  border: 2px dashed #cbd5e1;
  border-radius: var(--rm-radius-md);
  color: var(--rm-text-muted);
}
</style>

<div class="reports-container">
  <!-- هدر اصلی -->
  <header class="reports-hero">
    <h1>گزارش‌ها و آرشیو رسانه‌ای</h1>
    <p>مجموعه کامل گزارش‌ها، عکس‌ها، صوت‌ها و فیلم‌های برگزاری جلسات و رویدادها</p>
  </header>

  <!-- فیلترها و جست‌وجو -->
  <section class="reports-filters">
    <form method="get">
      <div class="filter-grid">
        {% for field in form %}
          <div class="filter-field">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
          </div>
        {% endfor %}
      </div>

      <div class="filter-actions">
        <div class="filter-count">
          نمایش موارد یافته شده
        </div>
        <div class="filter-buttons">
          {% if params %}
            <a href="?" class="btn-filter-reset">حذف فیلترها</a>
          {% endif %}
          <button type="submit" class="btn-filter-submit">اعمال فیلتر و جست‌وجو</button>
        </div>
      </div>
    </form>
  </section>

  <!-- لیست کارت‌ها -->
  <main class="cards-grid">
    {% for post in page.object_list %}
      <article class="report-card">
        {% if post.cover %}
          <div class="card-media">
            {% if post.get_kind_display %}
              <span class="card-kind-badge">{{ post.get_kind_display }}</span>
            {% endif %}
            <img src="{% url 'reports_media:cover' post.pk %}" alt="{{ post.title }}" class="card-cover" loading="lazy">
          </div>
        {% endif %}

        <div class="card-body">
          <h2 class="card-title">
            <a href="{% url 'reports_media:detail' post.pk %}">{{ post.title }}</a>
          </h2>

          {% if post.summary %}
            <p class="card-summary">{{ post.summary }}</p>
          {% endif %}

          <div class="meta-chips">
            <div class="meta-group">
              {% if post.category %}
                <span class="meta-chip category">{{ post.category.name }}</span>
              {% endif %}
              {% if post.event_date %}
                <span class="meta-chip">{{ post.event_date|date:"Y/m/d" }}</span>
              {% endif %}
            </div>
            <div class="meta-group">
              <span class="meta-chip">👁 {{ post.views }}</span>
            </div>
          </div>
        </div>
      </article>
    {% empty %}
      <div class="empty-state">
        <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" style="margin: 0 auto 1rem; opacity: 0.4;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"></path>
        </svg>
        <p style="font-size: 1.1rem; font-weight: 700; color: #475569; margin-bottom: 0.5rem;">هیچ گزارشی یافت نشد!</p>
        <p style="font-size: 0.85rem; margin: 0;">لطفاً کلمات کلیدی یا فیلترهای اعمال‌شده را تغییر دهید.</p>
      </div>
    {% endfor %}
  </main>

  <!-- صفحه‌بندی -->
  {% if page.has_other_pages %}
    <nav class="pagination-wrapper">
      {% if page.has_previous %}
        <a href="?page={{ page.previous_page_number }}{% if params %}&{{ params }}{% endif %}" class="page-btn">← صفحه قبل</a>
      {% endif %}

      <span class="page-info">صفحه {{ page.number }} از {{ page.paginator.num_pages }}</span>

      {% if page.has_next %}
        <a href="?page={{ page.next_page_number }}{% if params %}&{{ params }}{% endif %}" class="page-btn">صفحه بعد →</a>
      {% endif %}
    </nav>
  {% endif %}
</div>
{% endblock %}
"""


@require_safe
@never_cache
def archive(request):
    form = ArchiveFilters(request.GET or None)
    scope = unit_filter(request)
    posts = scope.apply(MediaPost.objects.visible(archived=True)).select_related('category').prefetch_related(
        'events', 'units', 'tags'
    )
    sort = 'newest'
    if form.is_bound:
        if form.is_valid():
            data = form.cleaned_data
            if term := data.get('q'):
                posts = posts.filter(
                    Q(title__icontains=term) |
                    Q(summary__icontains=term) |
                    Q(description__icontains=term) |
                    Q(tags__name__icontains=term)
                )
            for field, lookup in (
                ('date_from', 'event_date__gte'),
                ('date_to', 'event_date__lte'),
                ('kind', 'kind'),
                ('category', 'category'),
                ('event', 'events'),
                ('unit', 'units'),
            ):
                if data.get(field):
                    posts = posts.filter(**{lookup: data[field]})
            sort = data.get('sort') or sort
        else:
            posts = posts.none()

    page = Paginator(posts.distinct().order_by(*ORDER[sort]), 12).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    template = Template(ARCHIVE_TEMPLATE_STRING)
    context = Context({
        'request': request,
        'form': form,
        'page': page,
        'params': params.urlencode(),
        'scope': scope,
    })
    return HttpResponse(template.render(context))


@require_safe
@never_cache
def detail(request, pk):
    visible = MediaPost.objects.visible(archived=True)
    post = get_object_or_404(
        visible.select_related('category').prefetch_related('events', 'units', 'tags', 'attachments'),
        pk=pk
    )
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

        items.append({
            'attachment': attachment,
            'kind': kind,
            'online_url': url,
            'file_url': reverse('reports_media:file', args=[attachment.pk]) if attachment.file else None
        })

    return render(request, 'reports_media/detail.html', {
        'post': post,
        'items': items,
        'scope': unit_filter(request)
    })


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
    response = FileResponse(
        stream,
        content_type=mime,
        as_attachment='download' in request.GET or kind in {'document', 'download'}
    )
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
