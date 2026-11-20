from django.urls import path

from . import views


app_name = 'feedback_polls'
urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.submit, name='submit'),
    path('polls/<int:pk>/', views.poll_detail, name='poll'),
    path('polls/<int:pk>/vote/', views.vote, name='vote'),
]
