from datetime import timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from dorm_heiat.models import Unit, UnitType
from .models import Gathering, GatheringNotice, GatheringReport, ReportAsset


class GatheringTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        unit_type = UnitType.objects.create(name='Dorm')
        cls.parent = Unit.objects.create(name='Main dorm', unit_type=unit_type)
        cls.child = Unit.objects.create(name='Sisters', unit_type=unit_type, parent=cls.parent)
        cls.other = Unit.objects.create(name='Another dorm', unit_type=unit_type)
        cls.upcoming = Gathering.objects.create(title='Upcoming session', status=Gathering.Status.PUBLISHED,
                                                starts_at=timezone.now() + timedelta(days=1), venue='Hall')
        cls.upcoming.units.add(cls.parent, cls.child)
        cls.held = Gathering.objects.create(title='Past session', status=Gathering.Status.HELD,
                                            starts_at=timezone.now() - timedelta(days=1), venue='Hall')
        cls.held.units.add(cls.child)

    def test_unit_filter_upcoming_archive_and_home(self):
        GatheringNotice.objects.create(gathering=self.upcoming, title='Public notice', published=True)
        GatheringNotice.objects.create(gathering=self.upcoming, title='Future notice', published=True,
                                       published_at=timezone.now() + timedelta(hours=1))
        self.assertFalse(self.held.reports.exists())
        report = GatheringReport.objects.create(gathering=self.held, title='Public report', published=True)
        ReportAsset.objects.create(report=report, embed='https://www.aparat.com/v/abc123')
        url = reverse('night_gatherings:list')
        response = self.client.get(url, {'unit': self.parent.pk})
        self.assertContains(response, 'Upcoming session', count=1)
        self.assertContains(response, 'Public notice', count=1)
        self.assertNotContains(response, 'Future notice')
        self.assertNotContains(response, 'Past session')
        self.assertNotContains(self.client.get(url, {'unit': self.other.pk}), 'Upcoming session')
        self.assertContains(self.client.get(url, {'show': 'archive', 'unit': self.parent.pk}), 'Public report')
        response = self.client.get('/', {'unit': self.child.pk})
        self.assertContains(response, 'Public notice')
        self.assertContains(response, 'Public report')
        self.assertContains(self.client.get(self.held.get_absolute_url()), '/embed/videohash/abc123/')

    def test_scheduled_report_assets_and_hidden_gathering(self):
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            report = GatheringReport.objects.create(
                gathering=self.held, title='Scheduled report', published=True,
                published_at=timezone.now() + timedelta(hours=1),
            )
            asset = ReportAsset.objects.create(
                report=report, file=SimpleUploadedFile('notes.pdf', b'%PDF-1.4 test'),
            )
            url = reverse('night_gatherings:asset', args=[asset.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertNotContains(self.client.get(self.held.get_absolute_url()), 'Scheduled report')
            report.published_at = timezone.now() - timedelta(minutes=1)
            report.save()
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response['Content-Disposition'].startswith('attachment'))
            response.close()
            self.held.status = Gathering.Status.HIDDEN
            self.held.save()
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.get(self.held.get_absolute_url()).status_code, 404)

    def test_admin_requires_units_and_separate_publication_permission(self):
        user = get_user_model().objects.create_user(username='editor', is_staff=True)
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='night_gatherings', codename__in=['add_gathering', 'change_gathering'],
        ))
        self.client.force_login(user)
        add_url = reverse('staff_panel:night_gatherings_gathering_add')
        data = {
            'title': 'New gathering', 'description': 'Description', 'venue': 'Hall',
            'starts_at_0': '2026-11-20', 'starts_at_1': '20:00:00', 'status': 'published',
        }
        response = self.client.post(add_url, data)
        self.assertIn('units', response.context['adminform'].form.errors)
        self.assertEqual(self.client.post(add_url, {**data, 'units': [self.child.pk]}).status_code, 302)
        gathering = Gathering.objects.get(title='New gathering')
        self.assertEqual(gathering.status, Gathering.Status.DRAFT)
        self.assertEqual(self.client.get(gathering.get_absolute_url()).status_code, 404)
