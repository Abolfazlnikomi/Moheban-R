from django.contrib.admin.apps import AdminConfig


class SiteAdminConfig(AdminConfig):
    default_site = 'MohebanAE.admin_access.SiteAdmin'

    def ready(self):
        super().ready()
        from django.contrib import admin
        from django.contrib.auth.admin import GroupAdmin, UserAdmin
        from django.contrib.auth.models import Group, User
        from django.db.models.signals import post_migrate

        from .admin_access import ManageAccounts, ProtectFullAdminGroup, ProtectPrivilegedUsers
        from .admin_roles import ensure_full_admin_group

        class ManagedUserAdmin(ProtectPrivilegedUsers, ManageAccounts, UserAdmin):
            pass

        class ManagedGroupAdmin(ProtectFullAdminGroup, ManageAccounts, GroupAdmin):
            pass

        post_migrate.connect(ensure_full_admin_group, sender=self.apps.get_app_config('auth'),
                             dispatch_uid='ensure_full_admin_group')
        admin.site.unregister([User, Group])
        admin.site.register(User, ManagedUserAdmin)
        admin.site.register(Group, ManagedGroupAdmin)
