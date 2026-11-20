from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import FooterSettings


class FooterTests(TestCase):
    def test_footer_is_shared_and_optional_links_are_hidden(self):
        for name in ('home', 'login', 'announcements:list', 'feedback_polls:index'):
            response = self.client.get(reverse(name))
            self.assertContains(response, '<footer class="site-footer"', count=1)
            self.assertContains(response, 'درباره ما')
            self.assertContains(response, 'تماس با ما')
            self.assertNotContains(response, 'اینستاگرام هیئت')

    def test_admin_can_edit_footer_and_add_social_link(self):
        footer = FooterSettings.objects.get(pk=1)
        change_url = reverse('staff_panel:site_info_footersettings_change', args=[footer.pk])
        data = {
            'name': 'Updated group', 'goals': 'Updated goals', 'activities': 'Updated activities',
            'email': 'contact@example.org', 'channel_url': 'https://example.org/channel',
            'instagram_url': 'https://example.org/instagram',
        }
        user = User.objects.create_user(username='visitor', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.post(change_url, data).status_code, 403)
        self.client.force_login(User.objects.create_superuser(username='administrator'))
        self.assertEqual(self.client.post(change_url, data).status_code, 302)
        add_link = reverse('staff_panel:site_info_sociallink_add', args=[footer.pk])
        invalid = self.client.post(add_link, {'label': 'Invalid', 'url': 'ftp://example.org/', 'position': 1})
        self.assertIn('url', invalid.context['form'].errors)
        valid = self.client.post(add_link, {'label': 'Additional channel', 'url': 'https://example.org/other', 'position': 1})
        self.assertEqual(valid.status_code, 302)
        self.client.logout()
        for name in ('home', 'login', 'announcements:list'):
            response = self.client.get(reverse(name))
            for value in (*data.values(), 'Additional channel', 'https://example.org/other'):
                self.assertContains(response, value)
