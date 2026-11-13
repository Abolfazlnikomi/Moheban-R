from django.contrib import admin

from dorm_heiat.admin import EditorialAdmin
from .models import Announcement

admin.site.register(Announcement, EditorialAdmin)
