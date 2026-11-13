from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Group, Permission

FULL_ADMIN_GROUP = 'مدیران کامل'


def is_full_admin(user):
    if not user.is_active or not user.is_staff:
        return False
    if not hasattr(user, '_full_admin_group_member'):
        user._full_admin_group_member = user.groups.filter(name=FULL_ADMIN_GROUP).exists()
    return user._full_admin_group_member


class SiteModelBackend(ModelBackend):
    def _get_group_permissions(self, user_obj):
        if is_full_admin(user_obj):
            return Permission.objects.all()
        return super()._get_group_permissions(user_obj)


def ensure_full_admin_group(sender, using, **kwargs):
    Group.objects.using(using).get_or_create(name=FULL_ADMIN_GROUP)

