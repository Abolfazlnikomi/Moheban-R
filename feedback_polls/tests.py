from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Feedback, FeedbackCategory, Poll, Vote


class FeedbackTests(TestCase):
    def setUp(self):
        self.category = FeedbackCategory.objects.get(name='فاطمیه')
        self.other = FeedbackCategory.objects.get(name='خوابگاه‌ها')
        self.member = User.objects.create_user(username='member')
        self.index = reverse('feedback_polls:index')

    def test_member_submits_feedback_and_admin_controls_publication(self):
        submit = reverse('feedback_polls:submit')
        self.assertRedirects(self.client.get(submit), f'/login/?next={submit}')
        self.client.force_login(self.member)
        response = self.client.post(submit, {
            'category': self.category.pk, 'kind': Feedback.Kind.CRITIQUE, 'title': 'A new critique',
            'body': 'Content', 'status': Feedback.Status.APPROVED,
        })
        self.assertRedirects(response, self.index)
        entry = Feedback.objects.get()
        self.assertEqual(entry.author, self.member)
        self.assertEqual(entry.status, Feedback.Status.PENDING)
        edit = reverse('staff_panel:feedback_polls_feedback_change', args=[entry.pk])
        self.assertEqual(self.client.get(edit).status_code, 403)
        self.client.force_login(User.objects.create_superuser(username='administrator'))
        moderation = reverse('staff_panel:feedback_polls_feedback_changelist')
        self.assertContains(self.client.get(moderation, {'status': 'pending', 'category': self.category.pk}), entry.title)
        self.assertNotContains(self.client.get(moderation, {'status': 'approved'}), entry.title)
        self.assertNotContains(self.client.get(self.index), entry.title)
        self.assertEqual(self.client.post(edit, {
            'title': entry.title, 'body': entry.body, 'category': self.category.pk,
            'kind': entry.kind, 'status': Feedback.Status.APPROVED,
        }).status_code, 302)
        self.client.logout()
        self.assertContains(self.client.get(self.index), entry.title)
        self.assertNotContains(self.client.get(self.index, {'category': self.other.pk}), entry.title)
        self.client.force_login(User.objects.get(username='administrator'))
        delete = reverse('staff_panel:feedback_polls_feedback_delete', args=[entry.pk])
        self.assertEqual(self.client.post(delete).status_code, 302)
        self.assertNotContains(self.client.get(self.index), entry.title)

    def test_poll_publication_vote_scope_and_single_vote(self):
        poll = Poll.objects.create(question='Public question', category=self.category, status=Poll.Status.OPEN)
        option = poll.options.create(text='First')
        second = poll.options.create(text='Second')
        draft = Poll.objects.create(question='Draft poll', category=self.category)
        foreign = draft.options.create(text='Unrelated')
        draft.options.create(text='Another')
        poll_url = reverse('feedback_polls:poll', args=[poll.pk])
        vote_url = reverse('feedback_polls:vote', args=[poll.pk])
        self.assertContains(self.client.get(self.index), poll_url)
        self.assertEqual(self.client.get(reverse('feedback_polls:poll', args=[draft.pk])).status_code, 404)
        self.assertRedirects(self.client.post(vote_url, {'option': option.pk}), f'/login/?next={vote_url}')
        self.client.force_login(self.member)
        invalid = self.client.post(vote_url, {'option': foreign.pk})
        self.assertIn('option', invalid.context['form'].errors)
        self.assertFalse(Vote.objects.exists())
        self.assertRedirects(self.client.post(vote_url, {'option': option.pk}), poll_url)
        self.assertRedirects(self.client.post(vote_url, {'option': second.pk}), poll_url)
        self.assertEqual(Vote.objects.get().option, option)
        self.assertContains(self.client.get(poll_url), 'First: 1 رأی')
        poll.status = Poll.Status.CLOSED
        poll.save()
        self.assertEqual(self.client.post(vote_url, {'option': option.pk}).status_code, 404)
        self.client.logout()
        self.assertContains(self.client.get(poll_url), 'First: 1 رأی')
