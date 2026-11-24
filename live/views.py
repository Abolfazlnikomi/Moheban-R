
from django.shortcuts import render
from .models import LiveStream


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
