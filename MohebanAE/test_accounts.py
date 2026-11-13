from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .admin_roles import FULL_ADMIN_GROUP


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountTests(TestCase):
    password = 'a strong passphrase 72!'
    new_password = 'a distinct passphrase 83!'

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='member', password=self.password)

    def test_admin_panels_render_in_persian(self):
        self.client.force_login(get_user_model().objects.create_superuser(username='manager'))
        for namespace in ('admin', 'staff_panel'):
            index = self.client.get(reverse(f'{namespace}:index'))
            self.assertContains(index, '<html lang="fa" dir="rtl">')
            group_form = self.client.get(reverse(f'{namespace}:auth_group_add'))
            self.assertContains(group_form, 'انتشار تجمع شبانه')

    def test_login_redirects_and_inactive_account(self):
        self.assertRedirects(self.client.get('/account/'), '/login/?next=/account/')
        data = {'username': self.user.username, 'password': self.password}
        self.assertRedirects(self.client.post('/login/', {**data, 'next': '/password-change/'}), '/password-change/')
        self.client.logout()
        self.assertRedirects(self.client.post('/login/', {**data, 'next': 'https://example.org/'}), '/account/')
        self.client.logout()
        self.assertRedirects(self.client.post('/login/', data), '/account/')
        self.client.logout()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.post('/login/', data).status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_password_change_and_csrf_protected_logout(self):
        browser = Client(enforce_csrf_checks=True)
        self.assertRedirects(browser.get('/password-change/'), '/login/?next=/password-change/')
        browser.force_login(self.user)
        browser.get('/password-change/')
        csrf = browser.cookies['csrftoken'].value
        response = browser.post('/password-change/', {
            'old_password': self.password, 'new_password1': self.new_password,
            'new_password2': self.new_password, 'csrfmiddlewaretoken': csrf,
        })
        self.assertRedirects(response, '/password-change/done/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertEqual(browser.get('/account/').status_code, 200)
        self.assertEqual(browser.get('/logout/').status_code, 405)
        self.assertEqual(browser.post('/logout/').status_code, 403)
        response = browser.post('/logout/?next=/account/', {'csrfmiddlewaretoken': browser.cookies['csrftoken'].value})
        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', browser.session)

    def test_admin_requires_staff_and_relevant_permissions(self):
        user_list = reverse('staff_panel:auth_user_changelist')
        report_list = reverse('staff_panel:reports_media_mediapost_changelist')
        password_url = reverse('staff_panel:auth_user_password_change', args=[self.user.pk])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get('/staff/').status_code, 302)
        self.assertNotContains(self.client.get('/account/'), 'دسترسی‌های مدیریتی من')

        self.user.is_staff = True
        self.user.save()
        self.assertEqual(self.client.get('/staff/').status_code, 302)
        self.client.logout()
        response = self.client.post('/staff/login/', {'username': self.user.username, 'password': self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

        group = Group.objects.create(name='Report readers')
        group.permissions.add(
            Permission.objects.get(content_type__app_label='reports_media', codename='view_mediapost'),
            Permission.objects.get(content_type__app_label='auth', codename='change_user'),
        )
        self.user.groups.add(group)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get('/staff/').status_code, 200)
        dashboard = self.client.get('/account/')
        self.assertContains(dashboard, 'دسترسی‌های مدیریتی من')
        self.assertContains(dashboard, f'href="{report_list}" target="account-workspace"')
        self.assertContains(dashboard, 'class="account-permissions">مشاهده</span>')
        self.assertNotContains(dashboard, f'href="{user_list}"')
        self.assertNotContains(dashboard, 'href="/staff/"')
        self.assertEqual(dashboard.headers['X-Frame-Options'], 'DENY')
        report_response = self.client.get(report_list)
        self.assertEqual(report_response.status_code, 200)
        self.assertEqual(report_response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertEqual(self.client.get(user_list).status_code, 403)
        self.assertEqual(self.client.get(password_url).status_code, 403)

        self.client.force_login(get_user_model().objects.create_superuser(username='manager'))
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get(user_list).status_code, 200)
        self.assertEqual(self.client.get(password_url).status_code, 200)

    def test_full_admin_can_manage_accounts_and_use_custom_permissions(self):
        User = get_user_model()
        manager = User.objects.create_superuser(username='manager')
        staff = User.objects.create_user(username='delegated', password=self.password, is_staff=True)
        full_group = Group.objects.get(name=FULL_ADMIN_GROUP)
        staff.groups.add(full_group)
        self.assertTrue(staff.has_perm('reports_media.publish_mediapost'))
        self.assertTrue(staff.has_perm('registrations_campaigns.export_campaignentry'))
        self.assertFalse(staff.is_superuser)

        response = self.client.post('/staff/login/', {
            'username': staff.username, 'password': self.password, 'next': '/staff/',
        })
        self.assertRedirects(response, '/staff/')
        dashboard = self.client.get('/account/')
        self.assertContains(dashboard, 'مدیر کامل')
        self.assertContains(dashboard, 'انتشار')
        self.assertContains(dashboard, 'دریافت خروجی')
        self.assertContains(dashboard, 'href="/staff/auth/user/" target="account-workspace"')
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get(reverse('staff_panel:auth_group_changelist')).status_code, 200)
        add_url = reverse('staff_panel:auth_user_add')
        response = self.client.post(add_url, {
            'username': 'created-by-admin', 'usable_password': 'true',
            'password1': self.new_password, 'password2': self.new_password,
        })
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(username='created-by-admin')
        self.assertTrue(created.check_password(self.new_password))
        self.assertEqual(self.client.get(reverse('staff_panel:auth_user_password_change', args=[created.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('staff_panel:auth_user_password_change', args=[manager.pk])).status_code, 404)
        response = self.client.get(reverse('staff_panel:auth_user_change', args=[created.pk]))
        self.assertNotContains(response, f'<option value="{full_group.pk}">{FULL_ADMIN_GROUP}</option>')
        values = {
            'username': created.username, 'is_active': 'on', 'is_staff': 'on',
            'date_joined_0': '2026-01-01', 'date_joined_1': '12:00:00',
        }
        response = self.client.post(reverse('staff_panel:auth_user_change', args=[created.pk]), {
            **values, 'groups': full_group.pk,
        })
        self.assertIn('groups', response.context['adminform'].form.errors)
        response = self.client.post(reverse('staff_panel:auth_user_change', args=[created.pk]), {
            **values, 'is_superuser': 'on',
        })
        self.assertEqual(response.status_code, 302,
                         response.context['adminform'].form.errors if response.status_code == 200 else '')
        created.refresh_from_db()
        self.assertFalse(created.is_superuser)
        self.assertFalse(created.groups.filter(pk=full_group.pk).exists())

        staff.groups.remove(full_group)
        self.assertEqual(self.client.get('/staff/').status_code, 302)
        created.groups.add(full_group)
        created.is_staff = False
        created.save()
        self.assertFalse(User.objects.get(pk=created.pk).has_perm('reports_media.publish_mediapost'))
