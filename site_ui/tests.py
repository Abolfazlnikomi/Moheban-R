from pathlib import Path

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class AppPresentationTests(TestCase):
    def assert_app_page(self, route, template_name, *, args=()):
        owner = template_name.split('/')[0]
        response = self.client.get(reverse(route, args=args))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name)
        for template in response.templates:
            name = template.name or ''
            if '/' not in name or name.startswith('django/'):
                continue
            app_label = name.split('/')[0]
            self.assertIn(app_label, {owner, 'site_ui', 'site_info'}, name)
            expected = Path(apps.get_app_config(app_label).path, 'templates', name)
            self.assertEqual(Path(template.origin.name).resolve(), expected.resolve())

    def test_public_pages_use_their_own_app_templates(self):
        pages = (
            ('home', 'home_page/index.html'),
            ('login', 'accounts/login.html'),
            ('announcements:list', 'announcements/list.html'),
            ('reports_media:archive', 'reports_media/archive.html'),
            ('publications:list', 'publications/list.html'),
            ('feedback_polls:index', 'feedback_polls/index.html'),
            ('night_gatherings:list', 'night_gatherings/list.html'),
            ('registrations_campaigns:campaigns', 'registrations_campaigns/campaigns.html'),
            ('registrations_campaigns:volunteer', 'registrations_campaigns/volunteer.html'),
            ('live:live_page', 'live/live_page.html'),
            ('donations:page', 'donations/donation_page.html'),
        )
        for route, template_name in pages:
            with self.subTest(route=route):
                self.assert_app_page(route, template_name)

    def test_signed_in_pages_use_their_own_app_templates(self):
        staff = get_user_model().objects.create_superuser('staff-editor')
        self.client.force_login(staff)
        self.assert_app_page('account', 'accounts/account.html')
        self.assert_app_page('password_change', 'accounts/password_change.html')
        self.assert_app_page('experience_writing:index', 'experience_writing/index.html')
        self.assert_app_page('staff_panel:section', 'workspace/section.html', args=('reports_media',))
        self.assert_app_page('staff_panel:live_management', 'live/management.html')
        self.assert_app_page('reports_media:archive', 'reports_media/archive.html')

    def test_assets_are_found_in_the_owning_apps(self):
        assets = (
            'site_ui/base.css',
            'site_ui/Vazirmatn.woff2',
            'site_ui/account-portal.js',
            'home_page/courtyard-hero.webp',
            'home_page/landing.css',
            'home_page/donation-card.css',
            'donations/donation.css',
            'live/live.css',
            'live/management.css',
            'night_gatherings/gatherings.css',
            'site_info/footer.css',
            'site_info/images/social/eitaa.jpg',
        )
        for name in assets:
            with self.subTest(asset=name):
                app_label = name.split('/')[0]
                found = finders.find(name)
                self.assertIsNotNone(found)
                expected = Path(apps.get_app_config(app_label).path, 'static', name)
                self.assertEqual(Path(found).resolve(), expected.resolve())
