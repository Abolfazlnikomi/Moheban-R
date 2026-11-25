
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.admin import site
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from MohebanAE.workspace_registry import BY_MODEL
from .models import LiveStream
from .forms import LiveStreamForm
from MohebanAE.workspace_views import workspace_navigation


# صفحه عمومی پخش زنده سایت
def live_page(request):
    live_stream = LiveStream.objects.filter(
        is_active=True
    ).first()

    return render(
        request,
        'live/live_page.html',
        {
            'live_stream': live_stream
        }
    )


# صفحه مدیریت پخش زنده در پنل اختصاصی
@login_required
@require_http_methods(["GET", "POST"])
def live_management(request):

    if not (request.user.is_active and request.user.is_staff):
        raise PermissionDenied

    model_admin = site.get_model_admin(LiveStream)

    if not model_admin.has_view_permission(request):
        raise PermissionDenied

    live_stream = LiveStream.objects.first()

    if live_stream:
        if not model_admin.has_change_permission(request, live_stream):
            raise PermissionDenied
    else:
        if not model_admin.has_add_permission(request):
            raise PermissionDenied

    form = LiveStreamForm(
        request.POST or None,
        instance=live_stream
    )

    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)

        model_admin.save_model(
            request,
            obj,
            form,
            change=bool(live_stream)
        )

        messages.success(
            request,
            'اطلاعات پخش زنده با موفقیت ذخیره شد.'
        )

        return redirect('staff_panel:live_management')

    context = workspace_navigation(
        request,
        resource=BY_MODEL[LiveStream]
    )

    context.update({
        'form': form,
        'live_stream': live_stream,
    })

    return render(
        request,
        'live/management.html',
        context
    )
