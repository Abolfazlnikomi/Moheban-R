from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .forms import FeedbackForm, VoteForm
from .models import Feedback, FeedbackCategory, Poll, Vote


def visible_polls():
    return Poll.objects.exclude(status=Poll.Status.DRAFT).annotate(
        option_count=Count('options'),
    ).filter(option_count__gte=2).order_by('-created_at', '-pk')


@require_safe
def index(request):
    categories = list(FeedbackCategory.objects.all())
    selected = next((item for item in categories if str(item.pk) == request.GET.get('category')), None)
    oldest = request.GET.get('sort') == 'oldest'
    entries = Feedback.objects.filter(status=Feedback.Status.APPROVED).select_related('category')
    polls = visible_polls().select_related('category')
    if selected is not None:
        entries = entries.filter(category=selected)
        polls = polls.filter(category=selected)
    if oldest:
        entries = entries.order_by('created_at', 'pk')
    return render(request, 'feedback_polls/index.html', {
        'categories': categories, 'selected': selected, 'oldest': oldest,
        'polls': Paginator(polls, 12).get_page(request.GET.get('poll_page')),
        'page': Paginator(entries, 12).get_page(request.GET.get('page')),
    })


@never_cache
@login_required
@require_http_methods(('GET', 'HEAD', 'POST'))
def submit(request):
    form = FeedbackForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        entry = form.save(commit=False)
        entry.author = request.user
        entry.save()
        messages.success(request, 'بازخورد شما ثبت شد و پس از تأیید مدیر منتشر می‌شود.')
        return redirect('feedback_polls:index')
    return render(request, 'feedback_polls/form.html', {'form': form})


def render_poll(request, poll, form=None):
    voted = request.user.is_authenticated and Vote.objects.filter(poll=poll, user=request.user).exists()
    results = poll.options.annotate(total_votes=Count('votes')) if voted or poll.status == Poll.Status.CLOSED else None
    return render(request, 'feedback_polls/poll.html', {
        'poll': poll, 'results': results, 'voted': voted,
        'form': (form if form is not None else VoteForm(poll=poll))
        if request.user.is_authenticated and not voted and poll.status == Poll.Status.OPEN else None,
    })


@never_cache
@require_safe
def poll_detail(request, pk):
    return render_poll(request, get_object_or_404(visible_polls(), pk=pk))


@never_cache
@login_required
@require_POST
def vote(request, pk):
    with transaction.atomic():
        poll = get_object_or_404(Poll.objects.select_for_update(), pk=pk, status=Poll.Status.OPEN)
        if poll.options.count() < 2:
            raise Http404
        if Vote.objects.filter(poll=poll, user=request.user).exists():
            return redirect('feedback_polls:poll', pk=pk)
        form = VoteForm(request.POST, poll=poll)
        if form.is_valid():
            Vote.objects.get_or_create(poll=poll, user=request.user, defaults={'option': form.cleaned_data['option']})
            return redirect('feedback_polls:poll', pk=pk)
    return render_poll(request, poll, form)
