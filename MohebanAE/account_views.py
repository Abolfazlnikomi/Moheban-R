from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from .admin_access import PERMISSION_ACTIONS, staff_panel
from .admin_roles import is_full_admin


class SiteLogoutView(LogoutView):
    redirect_field_name = None


@method_decorator([never_cache, login_required], name='dispatch')
class AccountView(TemplateView):
    template_name = 'accounts/account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if staff_panel.has_permission(self.request):
            modules = staff_panel.get_app_list(self.request)
            for module in modules:
                for entry in module['models']:
                    opts = entry['model']._meta
                    entry['actions'] = [
                        PERMISSION_ACTIONS[action] for action, allowed in entry['perms'].items() if allowed
                    ]
                    entry['actions'].extend(
                        PERMISSION_ACTIONS[action] for action in ('publish', 'export')
                        if user.has_perm(f'{opts.app_label}.{action}_{opts.model_name}')
                    )
            context['management_modules'] = modules
            if user.is_superuser:
                context['management_level'] = 'مدیر کل'
            elif is_full_admin(user):
                context['management_level'] = 'مدیر کامل'
            else:
                context['management_level'] = 'کاربر دارای مجوز مدیریت'
        return context
