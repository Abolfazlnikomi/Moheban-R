from django.urls import path

from dorm_heiat.views import editorial_detail, editorial_list
from .models import Publication

app_name = 'publications'
options = {'model': Publication, 'label': 'نشریات'}
urlpatterns = [
    path('', editorial_list, options, name='list'),
    path('<int:pk>/', editorial_detail, options, name='detail'),
]

