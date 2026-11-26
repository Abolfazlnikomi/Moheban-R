from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('home_page.urls')),
    path('', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('staff/', include('workspace.urls')),

    # ماژول ادیتور متن پیشرفته CKEditor 5
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # ماژول گزارش‌ها و رسانه‌ها
    path('reports/', include('reports_media.urls')),

    path('announcements/', include('announcements.urls')),
    path('feedback/', include('feedback_polls.urls')),
    path('publications/', include('publications.urls')),
    path('night-gatherings/', include('night_gatherings.urls')),
    path('', include('registrations_campaigns.urls')),
    path('live/', include('live.urls')),
    path('donations/', include('donations.urls')),
]

# سرو فایل‌های مدیا و استاتیک در حالت DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
