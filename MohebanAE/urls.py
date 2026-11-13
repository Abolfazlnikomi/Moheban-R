from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from dorm_heiat.views import home

from .account_views import AccountView, SiteLogoutView

urlpatterns = [
    path('', home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', SiteLogoutView.as_view(), name='logout'),
    path('account/', AccountView.as_view(), name='account'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html',
    ), name='password_change_done'),
    path('admin/', admin.site.urls),
    path('staff/', include('MohebanAE.workspace_urls')),
    path('reports/', include('reports_media.urls')),
    path('announcements/', include('announcements.urls')),
    path('publications/', include('publications.urls')),
    path('night-gatherings/', include('night_gatherings.urls')),
    path('', include('registrations_campaigns.urls')),
]
