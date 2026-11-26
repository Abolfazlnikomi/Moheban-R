from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from announcements.models import Announcement
from night_gatherings.models import Gathering
from night_gatherings.views import upcoming_filter

from workspace.registry import workspace_navigation


class SiteLogoutView(LogoutView):
    redirect_field_name = None


@method_decorator([never_cache, login_required], name='dispatch')
class AccountView(TemplateView):
    template_name = 'accounts/account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            next_gathering=Gathering.visible().filter(upcoming_filter(), is_public=True).order_by('starts_at', 'pk').first(),
            recent_announcements=Announcement.visible().filter(is_public=True)[:3],
        )
        context.update(workspace_navigation(self.request))
        return context
