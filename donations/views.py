
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import DonationSettings


def donation_page(request):
    donation_settings = DonationSettings.objects.first()

    return render(
        request,
        "donations/donation_page.html",
        {
            "donation_settings": donation_settings,
        }
    )


@require_POST
def donation_payment(request):
    donation_settings = DonationSettings.objects.first()

    if not donation_settings or not donation_settings.payment_enabled:
        messages.warning(
            request,
            "درگاه پرداخت آنلاین در حال حاضر فعال نیست. "
            "لطفاً از روش کارت‌به‌کارت استفاده کنید."
        )
        return redirect("donations:page")

    # درگاه پرداخت در مراحل بعدی به این قسمت متصل خواهد شد.
    messages.info(
        request,
        "اتصال به درگاه پرداخت هنوز پیاده‌سازی نشده است."
    )

    return redirect("donations:page")
