from django.contrib import admin

from dorm_heiat.admin import EditorialAdmin
from .models import Publication

admin.site.register(Publication, EditorialAdmin)
