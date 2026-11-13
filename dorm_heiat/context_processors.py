from django.utils.functional import SimpleLazyObject

from .unit_filter import unit_filter


def unit_menu(request):
    return {'menu_scope': SimpleLazyObject(lambda: unit_filter(request))}

