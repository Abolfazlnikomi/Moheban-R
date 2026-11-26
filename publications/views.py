from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from dorm_heiat.unit_filter import unit_filter

from .models import Publication

LABEL = 'نشریات'


@require_safe
def publication_list(request):
    scope = unit_filter(request)
    page = Paginator(scope.apply(Publication.visible()), 12).get_page(request.GET.get('page'))
    return render(request, 'publications/list.html', {'scope': scope, 'page': page, 'label': LABEL})


@require_safe
def publication_detail(request, pk):
    item = get_object_or_404(Publication.visible().prefetch_related('units__parent', 'units__unit_type'), pk=pk)
    return render(request, 'publications/detail.html', {
        'item': item, 'label': LABEL, 'scope': unit_filter(request),
    })
