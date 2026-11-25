from django.contrib.auth.models import User
from django.urls import path
from django.views.generic import RedirectView
from live import views as live_views
from registrations_campaigns.models import Campaign, VolunteerApplication

from . import workspace_views as views
from .workspace_registry import RESOURCES


app_name = 'staff_panel'
urlpatterns = [
    path('', RedirectView.as_view(pattern_name='account')),
    path('login/', RedirectView.as_view(pattern_name='login'), name='login'),
    path('sections/<slug:section_key>/', views.section, name='section'),
    path('live/',live_views.live_management,name='live_management'),
]

for resource in RESOURCES:
    opts = resource.model._meta
    if resource.parent:
        parent_opts = resource.parent._meta
        base = f'{parent_opts.app_label}/{parent_opts.model_name}/<int:parent_pk>/{opts.model_name}/'
    else:
        base = f'{opts.app_label}/{opts.model_name}/'
    config = {'resource': resource}
    urlpatterns.extend([
        path(base, views.resource_list, config, name=f'{resource.key}_changelist'),
        path(base + 'add/', views.resource_form, config, name=f'{resource.key}_add'),
        path(base + '<int:pk>/', views.resource_detail, config, name=f'{resource.key}_detail'),
        path(base + '<int:pk>/change/', views.resource_form, config, name=f'{resource.key}_change'),
        path(base + '<int:pk>/delete/', views.resource_delete, config, name=f'{resource.key}_delete'),
    ])
    if resource.model is User:
        urlpatterns.append(path(base + '<int:pk>/password/', views.user_password,
                                name=f'{resource.key}_password_change'))
    elif resource.model is Campaign:
        urlpatterns.append(path(base + '<int:pk>/export/', views.export_campaign,
                                name=f'{resource.key}_export'))
    elif resource.model is VolunteerApplication:
        urlpatterns.append(path(base + 'export/', views.export_volunteers, name=f'{resource.key}_export'))
