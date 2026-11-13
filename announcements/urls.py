from django.urls import path

from dorm_heiat.views import editorial_detail, editorial_list
from .models import Announcement

app_name = 'announcements'
options = {'model': Announcement, 'label': 'اطلاعیه‌ها'}
urlpatterns = [
    path('', editorial_list, options, name='list'),
    path('<int:pk>/', editorial_detail, options, name='detail'),
]

