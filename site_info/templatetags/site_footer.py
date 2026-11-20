from django import template

from site_info.models import FooterSettings

register = template.Library()


@register.inclusion_tag('site_info/footer.html')
def site_footer():
    settings = FooterSettings.objects.prefetch_related('links').filter(pk=1).first()
    return {'footer_settings': settings, 'social_links': settings.links.all() if settings else ()}
