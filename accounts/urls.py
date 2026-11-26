from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import AccountView, SiteLogoutView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', SiteLogoutView.as_view(), name='logout'),
    path('account/', AccountView.as_view(), name='account'),
    path('account/experiences/', include('experience_writing.urls')),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html',
    ), name='password_change_done'),
]
