from django.urls import path

from . import views

app_name = 'registrations_campaigns'
urlpatterns = [
    path('volunteer/', views.volunteer, name='volunteer'),
    path('campaigns/', views.campaigns, name='campaigns'),
    path('campaigns/<int:pk>/', views.campaign_detail, name='detail'),
    path('campaigns/<int:pk>/banner/', views.campaign_banner, name='banner'),
]

