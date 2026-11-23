from django.urls import path

from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.listing, name='list'),
    path('archive/', views.listing, {'archived': True}, name='archive'),
    path('images/<int:pk>/', views.image, name='image'),
    path('covers/<int:pk>/', views.cover, name='cover'),
    path('<int:pk>/', views.detail, name='detail'),
]
