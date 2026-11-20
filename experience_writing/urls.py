from django.urls import path

from . import views


app_name = 'experience_writing'
urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
]
