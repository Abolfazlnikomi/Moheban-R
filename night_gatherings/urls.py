from django.urls import path

from . import views

app_name = 'night_gatherings'
urlpatterns = [
    path('', views.listing, name='list'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/poster/', views.poster, name='poster'),
    path('notices/<int:pk>/poster/', views.notice_poster, name='notice_poster'),
    path('assets/<int:pk>/', views.asset, name='asset'),
]

