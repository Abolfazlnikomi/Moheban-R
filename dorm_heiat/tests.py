from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.test import RequestFactory, TestCase
from django.utils import timezone

from announcements.models import Announcement
from publications.models import Publication
from registrations_campaigns.models import Campaign
from reports_media.models import Category, MediaPost
from .models import Unit, UnitType


class UnitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        kind = UnitType.objects.create(name='Dorm')
        cls.parent = Unit.objects.create(name='Parent', unit_type=kind)
        cls.child = Unit.objects.create(name='Sisters', unit_type=kind, parent=cls.parent,
                                        audience=Unit.Audience.SISTERS)
        cls.other = Unit.objects.create(name='Brothers', unit_type=kind, parent=cls.parent,
                                        audience=Unit.Audience.BROTHERS)

    def test_cycle_is_rejected(self):
        self.parent.parent = self.child
        with self.assertRaises(ValidationError):
            self.parent.full_clean()

    def test_home_renders_landing_and_menu_without_content(self):
        response = self.client.get('/')
        self.assertContains(response, '<details class="site-menu">')
        self.assertContains(response, '<title>هیئت محبان اهل‌بیت علیهم‌السلام</title>')
        self.assertContains(response, 'id="about"')
        self.assertContains(response, '<footer class="landing-footer">')
        for path in ('/announcements/', '/reports/', '/publications/', '/campaigns/', '/volunteer/', '/login/'):
            self.assertContains(response, f'href="{path}"')

    def test_landing_uses_local_assets_and_submits_the_selected_unit(self):
        response = self.client.get('/', {'unit': self.child.pk})
        for asset in ('site/fonts.css', 'site/landing.css', 'site/courtyard-hero.webp'):
            self.assertContains(response, static(asset))
            self.assertIsNotNone(finders.find(asset))
        self.assertIsNotNone(finders.find('site/Vazirmatn.woff2'))
        self.assertContains(response, 'action="#content"')
        self.assertContains(response, f'<option value="{self.child.pk}" selected>')
        self.assertContains(response, f'href="/volunteer/?unit={self.child.pk}"')
        self.assertContains(response, f'href="/night-gatherings/?show=archive&amp;unit={self.child.pk}"')

    def test_menu_lists_active_units_on_pages_without_a_unit_filter(self):
        self.other.active = False
        self.other.save()
        response = self.client.get('/login/', {'unit': self.child.pk})
        self.assertContains(response, f'href="/?unit={self.parent.pk}">Parent</a>')
        self.assertContains(response, f'href="/?unit={self.child.pk}" aria-current="true">— Sisters</a>')
        self.assertNotContains(response, f'href="/?unit={self.other.pk}"')

    def test_shared_filter_and_duplicates(self):
        today = timezone.localdate()
        announcement = Announcement.objects.create(title='Child announcement', published=True, is_public=False)
        announcement.units.add(self.parent, self.child)
        Publication.objects.create(title='General publication', published=True)
        campaign = Campaign.objects.create(title='Child campaign', description='Text',
                                           starts_on=today, ends_on=today, status=Campaign.Status.ACTIVE)
        campaign.units.add(self.child)
        post = MediaPost.objects.create(title='Child report', event_date=today, kind=MediaPost.Kind.REPORT,
                                        category=Category.objects.create(name='Report'), status=MediaPost.Status.PUBLISHED)
        post.units.add(self.child)

        response = self.client.get('/', {'unit': self.parent.pk})
        self.assertContains(response, 'Child announcement', count=1)
        self.assertContains(response, 'Child report')
        self.assertContains(response, 'Child campaign')
        self.assertNotContains(response, 'General publication')
        self.assertContains(response, f'/reports/?unit={self.parent.pk}')
        for url, title in [('/announcements/', announcement.title), ('/reports/', post.title),
                           ('/campaigns/', campaign.title)]:
            self.assertContains(self.client.get(url, {'unit': self.child.pk}), title, count=1)
            self.assertNotContains(self.client.get(url, {'unit': self.other.pk}), title)
        self.assertNotContains(self.client.get('/announcements/', {'unit': 'public'}), announcement.title)
        self.assertContains(self.client.get('/publications/', {'unit': 'public'}), 'General publication')
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 200)

    def test_inactive_unit_keeps_its_old_links(self):
        announcement = Announcement.objects.create(title='Old article', published=True, is_public=False)
        announcement.units.add(self.child)
        self.child.active = False
        self.child.save()
        request = RequestFactory().get('/admin/')
        request.user = get_user_model().objects.create_superuser(username='manager')
        manager = admin.site._registry[Announcement]
        new_form = manager.get_form(request)()
        old_form = manager.get_form(request, announcement)(instance=announcement)
        self.assertNotIn(self.child, new_form.fields['units'].queryset)
        self.assertIn(self.child, old_form.fields['units'].queryset)
        self.assertNotContains(self.client.get('/announcements/'), f'<option value="{self.child.pk}"')
        self.assertNotContains(self.client.get('/announcements/', {'unit': self.parent.pk}), announcement.title)
        self.assertContains(self.client.get(announcement.get_absolute_url()), announcement.title)
