from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from announcements.models import Announcement
from night_gatherings.models import Gathering
from night_gatherings.views import upcoming_filter

from .admin_roles import is_full_admin
from .workspace_registry import workspace_modules


class SiteLogoutView(LogoutView):
    redirect_field_name = None


@method_decorator([never_cache, login_required], name='dispatch')
class AccountView(TemplateView):
    template_name = 'accounts/account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update(
            next_gathering=Gathering.visible().filter(upcoming_filter(), is_public=True).order_by('starts_at', 'pk').first(),
            recent_announcements=Announcement.visible().filter(is_public=True)[:3],
        )
        modules = workspace_modules(self.request)
        if modules:
            context['management_modules'] = modules
            if user.is_superuser:
                context['management_level'] = 'مدیر کل'
            elif is_full_admin(user):
                context['management_level'] = 'مدیر کامل'
            else:
                context['management_level'] = 'کاربر دارای مجوز مدیریت'
        return context
