from django.urls import path

from . import views

app_name = 'reports_media'
urlpatterns = [
    path('', views.archive, name='archive'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/cover/', views.cover, name='cover'),
    path('files/<int:pk>/', views.attachment, name='file'),
]

