from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe
from django.urls import reverse

from dorm_heiat.models import discoverable
from dorm_heiat.unit_filter import unit_filter

from .forms import CampaignEntryForm, VolunteerForm
from .models import Campaign, VolunteerSection, VolunteerSettings


def public_campaigns():
    return discoverable(Campaign.objects.exclude(status=Campaign.Status.INACTIVE))


@never_cache
@require_http_methods(['GET', 'HEAD', 'POST'])
def volunteer(request):
    scope = unit_filter(request)
    settings = VolunteerSettings.objects.filter(pk=1, enabled=True).first()
    form = None
    if settings and VolunteerSection.objects.filter(active=True).exists():
        form = VolunteerForm(request.POST if request.method == 'POST' else None, settings=settings)
        if request.method == 'POST' and form.is_valid():
            form.save()
            messages.success(request, 'درخواست خادمی ثبت شد و در انتظار بررسی است.')
            return redirect(reverse('registrations_campaigns:volunteer') + scope.query)
    return render(request, 'registrations_campaigns/volunteer.html', {'form': form, 'scope': scope},
                  status=403 if request.method == 'POST' and form is None else 200)


@require_safe
def campaigns(request):
    scope = unit_filter(request)
    page = Paginator(scope.apply(public_campaigns()), 12).get_page(request.GET.get('page'))
    return render(request, 'registrations_campaigns/campaigns.html', {'page': page, 'scope': scope})


@never_cache
@require_http_methods(['GET', 'HEAD', 'POST'])
def campaign_detail(request, pk):
    campaign = get_object_or_404(public_campaigns(), pk=pk)
    scope = unit_filter(request)
    form = None
    if campaign.is_open and campaign.participation == Campaign.Participation.FORM:
        form = CampaignEntryForm(request.POST if request.method == 'POST' else None, campaign=campaign)
        if request.method == 'POST' and form.is_valid():
            form.save()
            messages.success(request, 'مشارکت شما ثبت شد.')
            return redirect(reverse('registrations_campaigns:detail', args=[pk]) + scope.query)
    return render(request, 'registrations_campaigns/detail.html', {'campaign': campaign, 'form': form, 'scope': scope},
                  status=403 if request.method == 'POST' and form is None else 200)


@never_cache
@require_safe
def campaign_banner(request, pk):
    user = request.user
    queryset = Campaign.objects.all() if user.is_staff and (
        user.has_perm('registrations_campaigns.view_campaign')
        or user.has_perm('registrations_campaigns.change_campaign')
    ) else public_campaigns()
    campaign = get_object_or_404(queryset, pk=pk)
    if not campaign.banner:
        raise Http404
    try:
        response = FileResponse(campaign.banner.open('rb'))
    except FileNotFoundError as error:
        raise Http404 from error
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return response
