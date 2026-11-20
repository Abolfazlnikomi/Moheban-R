from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Experience, ExperienceAccess, Scope, Subgroup


class ExperienceTests(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(username='writer')
        self.scope = Scope.objects.create(name='Fatemiyeh')
        self.other = Scope.objects.create(name='Private other scope')
        self.subgroup = Subgroup.objects.create(scope=self.scope, name='Weekly')
        self.hidden_subgroup = Subgroup.objects.create(scope=self.other, name='Private media')
        self.allowed = Experience.objects.create(subgroup=self.subgroup, title='Allowed experience', body='Visible')
        self.hidden = Experience.objects.create(
            subgroup=self.hidden_subgroup, title='Hidden experience', body='Private body',
        )
        self.index_url = reverse('experience_writing:index')
        self.create_url = reverse('experience_writing:create')

    def enable(self):
        grant = ExperienceAccess.objects.create(user=self.member, enabled=True)
        grant.scopes.add(self.scope)
        return grant

    def test_private_pages_require_login_and_explicit_flag(self):
        hidden_url = reverse('experience_writing:detail', args=[self.hidden.pk])
        for url in (self.index_url, self.create_url, hidden_url):
            self.assertRedirects(self.client.get(url), f'/login/?next={url}')
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get(reverse('home')), self.index_url)
        self.assertNotContains(self.client.get(reverse('account')), self.index_url)
        self.assertEqual(self.client.get(self.index_url).status_code, 403)
        grant = self.enable()
        self.assertContains(self.client.get(reverse('account')), self.index_url)
        self.assertNotContains(self.client.get(reverse('home')), self.index_url)
        response = self.client.get(self.index_url)
        self.assertContains(response, self.allowed.title)
        self.assertNotContains(response, self.hidden.title)
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertEqual(self.client.get(hidden_url).status_code, 404)
        grant.scopes.clear()
        self.assertNotContains(self.client.get(self.index_url), self.allowed.title)
        self.assertEqual(self.client.post(self.create_url).status_code, 403)
        grant.enabled = False
        grant.save()
        self.assertEqual(self.client.get(self.index_url).status_code, 403)

    def test_member_can_only_record_in_assigned_consistent_scope(self):
        grant = self.enable()
        self.client.force_login(self.member)
        data = {'scope': self.scope.pk, 'subgroup': self.subgroup.pk, 'title': 'New experience', 'body': 'Share this'}
        form = self.client.get(self.create_url)
        self.assertContains(form, 'موضوع اصلی')
        self.assertNotContains(form, self.hidden_subgroup.name)
        rejected = self.client.post(self.create_url, {**data, 'subgroup': self.hidden_subgroup.pk})
        self.assertIn('subgroup', rejected.context['form'].errors)
        self.assertFalse(Experience.objects.filter(title=data['title']).exists())
        grant.scopes.add(self.other)
        mismatched = self.client.post(self.create_url, {**data, 'subgroup': self.hidden_subgroup.pk})
        self.assertIn('subgroup', mismatched.context['form'].errors)
        saved = self.client.post(self.create_url, {**data, 'author': 999999})
        item = Experience.objects.get(title=data['title'])
        self.assertEqual(item.author, self.member)
        self.assertIsNotNone(item.recorded_at)
        self.assertRedirects(saved, reverse('experience_writing:detail', args=[item.pk]))

    def test_superuser_can_assign_scope_on_existing_account(self):
        self.client.force_login(User.objects.create_superuser(username='administrator'))
        self.assertContains(self.client.get(self.index_url), self.hidden.title)
        self.assertContains(self.client.get(reverse('admin:experience_writing_scope_add')), 'subgroups-TOTAL_FORMS')
        user_url = reverse('admin:auth_user_change', args=[self.member.pk])
        response = self.client.get(user_url)
        formset = response.context['inline_admin_formsets'][0].formset
        prefix = formset.prefix
        self.assertContains(response, f'{prefix}-0-enabled')
        result = self.client.post(user_url, {
            'username': self.member.username, 'is_active': 'on',
            'date_joined_0': '2026-01-01', 'date_joined_1': '12:00:00',
            f'{prefix}-TOTAL_FORMS': 1, f'{prefix}-INITIAL_FORMS': 0,
            f'{prefix}-0-enabled': 'on', f'{prefix}-0-scopes': [self.scope.pk, self.other.pk],
        })
        self.assertEqual(result.status_code, 302)
        grant = ExperienceAccess.objects.get(user=self.member)
        self.assertTrue(grant.enabled)
        self.assertCountEqual(grant.scopes.all(), [self.scope, self.other])
