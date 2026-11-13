from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from announcements.models import Announcement
from dorm_heiat.models import Unit, UnitType
from night_gatherings.models import Gathering, GatheringReport, ReportAsset

from .admin_roles import FULL_ADMIN_GROUP
from .workspace_registry import RESOURCES


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountTests(TestCase):
    password = 'a strong passphrase 72!'
    new_password = 'a distinct passphrase 83!'

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='member', password=self.password)

    def test_admin_and_custom_workspace_render_in_persian(self):
        self.client.force_login(get_user_model().objects.create_superuser(username='manager'))
        for namespace in ('admin', 'staff_panel'):
            index = self.client.get(reverse(f'{namespace}:index'))
            self.assertContains(index, '<html lang="fa" dir="rtl">')
            group_form = self.client.get(reverse(f'{namespace}:auth_group_add'))
            self.assertContains(group_form, 'انتشار تجمع شبانه')
            if namespace == 'staff_panel':
                self.assertTemplateUsed(index, 'workspace/index.html')
                self.assertTemplateUsed(group_form, 'workspace/form.html')
                self.assertNotContains(group_form, '/static/admin/')

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

    def test_member_dashboard_loads_its_own_theme_and_account_actions(self):
        self.client.force_login(self.user)
        dashboard = self.client.get(reverse('account'))
        for asset in ('site/account-dashboard.css', 'site/account-portal.css', 'site/account-portal.js', 'site/mihrab.svg'):
            self.assertContains(dashboard, static(asset))
            self.assertIsNotNone(finders.find(asset))
        self.assertContains(dashboard, 'id="account-menu"')
        self.assertContains(dashboard, 'aria-controls="account-menu"')
        self.assertContains(dashboard, 'href="#account-security"')
        self.assertContains(dashboard, 'action="/logout/"')
        self.assertNotContains(dashboard, 'id="site-nav"')
        self.assertContains(dashboard, '<bdi>member</bdi>')
        self.assertContains(dashboard, f'href="{reverse("password_change")}"')
        self.assertNotContains(dashboard, 'href="/staff/"')
        self.assertNotContains(self.client.get(reverse('home')), static('site/account-portal.css'))

    def test_member_dashboard_lists_only_public_announcements_and_next_public_gathering(self):
        now = timezone.now()
        unit = Unit.objects.create(name='Public unit', unit_type=UnitType.objects.create(name='Unit type'))
        for title, days, is_public, status in (
            ('Next public gathering', 2, True, Gathering.Status.PUBLISHED),
            ('Later public gathering', 3, True, Gathering.Status.PUBLISHED),
            ('Earlier scoped gathering', 1, False, Gathering.Status.PUBLISHED),
            ('Past public gathering', -1, True, Gathering.Status.PUBLISHED),
            ('Draft public gathering', 1, True, Gathering.Status.DRAFT),
        ):
            gathering = Gathering.objects.create(
                title=title, is_public=is_public, status=status, venue='Hall', starts_at=now + timedelta(days=days),
            )
            gathering.units.add(unit)
        Announcement.objects.create(title='Public notice', published=True)
        scoped = Announcement.objects.create(title='Scoped notice', published=True, is_public=False)
        scoped.units.add(unit)
        Announcement.objects.create(title='Scheduled notice', published=True, published_at=now + timedelta(days=1))
        self.client.force_login(self.user)
        dashboard = self.client.get(reverse('account'))
        self.assertContains(dashboard, 'Next public gathering')
        self.assertContains(dashboard, 'Public notice')
        for title in ('Later public gathering', 'Earlier scoped gathering', 'Past public gathering',
                      'Draft public gathering', 'Scoped notice', 'Scheduled notice'):
            self.assertNotContains(dashboard, title)

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
        self.assertEqual(self.client.get('/staff/').status_code, 403)
        self.assertNotContains(self.client.get('/account/'), 'دسترسی‌های مدیریتی من')

        self.user.is_staff = True
        self.user.save()
        self.assertEqual(self.client.get('/staff/').status_code, 403)
        self.client.logout()
        self.assertRedirects(self.client.get('/staff/'), '/login/?next=/staff/')

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
        self.assertContains(dashboard, f'href="{report_list}"')
        self.assertContains(dashboard, 'class="account-permissions">مشاهده</span>')
        self.assertNotContains(dashboard, f'href="{user_list}"')
        self.assertContains(dashboard, 'href="/staff/"')
        self.assertNotContains(dashboard, '<iframe')
        self.assertNotContains(dashboard, 'href="/admin/')
        self.assertEqual(dashboard.headers['X-Frame-Options'], 'DENY')
        report_response = self.client.get(report_list)
        self.assertEqual(report_response.status_code, 200)
        self.assertTemplateUsed(report_response, 'workspace/list.html')
        self.assertEqual(report_response.headers['X-Frame-Options'], 'DENY')
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

        response = self.client.post('/login/', {
            'username': staff.username, 'password': self.password, 'next': '/staff/',
        })
        self.assertRedirects(response, '/staff/')
        dashboard = self.client.get('/account/')
        self.assertContains(dashboard, 'مدیر کامل')
        self.assertContains(dashboard, 'انتشار')
        self.assertContains(dashboard, 'دریافت خروجی')
        self.assertContains(dashboard, 'href="/staff/auth/user/"')
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get(reverse('staff_panel:auth_group_changelist')).status_code, 200)
        add_url = reverse('staff_panel:auth_user_add')
        response = self.client.post(add_url, {
            'username': 'created-by-admin',
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
        self.assertIn('groups', response.context['form'].errors)
        response = self.client.post(reverse('staff_panel:auth_user_change', args=[created.pk]), {
            **values, 'is_superuser': 'on',
        })
        self.assertEqual(response.status_code, 302,
                         response.context['form'].errors if response.status_code == 200 else '')
        created.refresh_from_db()
        self.assertFalse(created.is_superuser)
        self.assertFalse(created.groups.filter(pk=full_group.pk).exists())

        staff.groups.remove(full_group)
        self.assertEqual(self.client.get('/staff/').status_code, 403)
        created.groups.add(full_group)
        created.is_staff = False
        created.save()
        self.assertFalse(User.objects.get(pk=created.pk).has_perm('reports_media.publish_mediapost'))

    def test_workspace_renders_native_list_and_form_for_every_top_level_resource(self):
        self.client.force_login(get_user_model().objects.create_superuser(username='manager'))
        for resource in RESOURCES:
            if resource.parent is not None:
                continue
            with self.subTest(resource=resource.key):
                response = self.client.get(resource.url('changelist'))
                self.assertTemplateUsed(response, 'workspace/list.html')
                self.assertNotContains(response, '/static/admin/')
                form_response = self.client.get(resource.url('add'))
                if resource.model._meta.model_name in ('campaignentry', 'volunteerapplication'):
                    self.assertEqual(form_response.status_code, 403)
                else:
                    self.assertTemplateUsed(form_response, 'workspace/form.html')

    def test_workspace_creates_searches_edits_and_confirms_deletion(self):
        self.user.is_staff = True
        self.user.save()
        self.user.user_permissions.add(*Permission.objects.filter(content_type__model='announcement',
                                                                  content_type__app_label='announcements'))
        self.client.force_login(self.user)
        prefix = 'staff_panel:announcements_announcement_'
        data = {
            'title': 'Needle announcement', 'description': 'Details', 'is_public': 'on',
            'published_at': timezone.localtime().strftime('%Y-%m-%dT%H:%M:%S'),
        }
        result = self.client.post(reverse(prefix + 'add'), data)
        announcement = Announcement.objects.get()
        detail_url = reverse(prefix + 'detail', args=[announcement.pk])
        self.assertRedirects(result, detail_url)
        list_url = reverse(prefix + 'changelist')
        self.assertContains(self.client.get(list_url, {'q': 'needle'}), announcement.title)
        self.assertNotContains(self.client.get(list_url, {'q': 'missing'}), announcement.title)
        result = self.client.post(reverse(prefix + 'change', args=[announcement.pk]), {**data, 'title': 'Changed'})
        self.assertRedirects(result, detail_url)
        self.assertContains(self.client.get(detail_url), 'Changed')
        delete_url = reverse(prefix + 'delete', args=[announcement.pk])
        self.assertTemplateUsed(self.client.get(delete_url), 'workspace/delete.html')
        self.assertTrue(Announcement.objects.filter(pk=announcement.pk).exists())
        self.assertRedirects(self.client.post(delete_url), list_url)
        self.assertFalse(Announcement.objects.filter(pk=announcement.pk).exists())

    def test_related_asset_requires_parent_permissions_and_stays_in_its_parent(self):
        gathering = Gathering.objects.create(title='Gathering', starts_at=timezone.now(), venue='Hall')
        report = GatheringReport.objects.create(gathering=gathering, title='Report')
        other = GatheringReport.objects.create(gathering=gathering, title='Other report')
        self.user.is_staff = True
        self.user.save()
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='night_gatherings',
            codename__in=['add_reportasset', 'view_reportasset', 'change_reportasset', 'view_gatheringreport'],
        ))
        self.client.force_login(self.user)
        prefix = 'staff_panel:night_gatherings_reportasset_'
        add_url = reverse(prefix + 'add', args=[report.pk])
        values = {'embed': 'https://www.aparat.com/v/abc123', 'caption': 'Clip', 'order': 0, 'report': other.pk}
        self.assertEqual(self.client.post(add_url, values).status_code, 403)
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label='night_gatherings', codename='change_gatheringreport',
        ))
        response = self.client.post(add_url, values)
        asset = ReportAsset.objects.get(report=report)
        self.assertRedirects(response, reverse(prefix + 'detail', args=[report.pk, asset.pk]))
        self.assertEqual(self.client.get(reverse(prefix + 'detail', args=[other.pk, asset.pk])).status_code, 404)
        asset.file = 'private-storage/cover.jpg'
        asset.save()
        change_url = reverse(prefix + 'change', args=[report.pk, asset.pk])
        response = self.client.get(change_url)
        self.assertContains(response, 'cover.jpg')
        self.assertNotContains(response, 'private-storage/')
        self.assertNotContains(response, '<iframe')
