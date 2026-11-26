from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from .access import experience_access
from .forms import ExperienceForm
from .models import Experience, Subgroup


def private_experience_view(view):
    @never_cache
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        scopes = experience_access(request)
        if scopes is None:
            raise PermissionDenied
        return view(request, scopes, *args, **kwargs)
    return wrapped


def render_experience(request, template, **context):
    from workspace.registry import workspace_navigation

    return render(request, f'experience_writing/{template}.html', {**workspace_navigation(request), **context})


def visible_experiences(scopes):
    return Experience.objects.filter(subgroup__scope__in=scopes).select_related('subgroup__scope', 'author')


@private_experience_view
@require_safe
def index(request, scopes):
    page = Paginator(visible_experiences(scopes), 20).get_page(request.GET.get('page'))
    return render_experience(
        request, 'index', page=page, scopes=scopes,
        can_record=Subgroup.objects.filter(scope__in=scopes).exists(),
    )


@private_experience_view
@require_http_methods(('GET', 'HEAD', 'POST'))
def create(request, scopes):
    if not Subgroup.objects.filter(scope__in=scopes).exists():
        raise PermissionDenied
    form = ExperienceForm(request.POST if request.method == 'POST' else None, scopes=scopes)
    if request.method == 'POST' and form.is_valid():
        experience = form.save(commit=False)
        experience.author = request.user
        experience.save()
        return redirect('experience_writing:detail', pk=experience.pk)
    return render_experience(request, 'form', form=form)


@private_experience_view
@require_safe
def detail(request, scopes, pk):
    experience = get_object_or_404(visible_experiences(scopes), pk=pk)
    return render_experience(request, 'detail', experience=experience)
