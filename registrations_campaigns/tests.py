from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from io import BytesIO

from openpyxl import load_workbook

from .models import Campaign, CampaignEntry, CampaignField, VolunteerApplication, VolunteerSection, VolunteerSettings


class RegistrationTests(TestCase):
    def test_volunteer_switch_and_validation(self):
        url = reverse('registrations_campaigns:volunteer')
        section = VolunteerSection.objects.create(name='Media')
        data = dict(first_name='Ali', last_name='Test', national_id='۰۰۱۳۵۴۰۸۲۳', phone='+989123456789',
                    section=section.pk)
        self.assertEqual(self.client.post(url, data).status_code, 403)
        VolunteerSettings.objects.create(enabled=True, require_birth_date=False, require_skills=True)
        self.assertIn('skills', self.client.post(url, data).context['form'].errors)
        data.update(skills='Photo', national_id='۰۰۰۰۰۰۰۰۰۰')
        self.assertIn('national_id', self.client.post(url, data).context['form'].errors)
        data['national_id'] = '۰۰۱۳۵۴۰۸۲۳'
        self.assertRedirects(self.client.post(url, data), url)
        entry = VolunteerApplication.objects.get()
        self.assertEqual(entry.phone, '09123456789')
        self.assertEqual(entry.status, VolunteerApplication.Status.PENDING)
        self.assertFalse(get_user_model().objects.exists())

    def test_campaign_form_and_export(self):
        today = timezone.localdate()
        campaign = Campaign.objects.create(title='Test', description='Description', status=Campaign.Status.ACTIVE,
                                            starts_on=today, ends_on=today)
        field = CampaignField.objects.create(campaign=campaign, label='Options', kind=CampaignField.Kind.CHOICE,
                                             required=True, options='First\nSecond')
        url = reverse('registrations_campaigns:detail', args=[campaign.pk])
        data = {'full_name': '=1+1', 'phone': '09123456789', f'custom_{field.pk}': 'Other'}
        self.assertIn(f'custom_{field.pk}', self.client.post(url, data).context['form'].errors)
        data[f'custom_{field.pk}'] = 'First'
        self.assertRedirects(self.client.post(url, data), url)
        self.assertEqual(CampaignEntry.objects.get().answers[0]['value'], 'First')
        self.assertFalse(get_user_model().objects.exists())
        campaign.starts_on = campaign.ends_on = today - timedelta(days=1)
        campaign.save()
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(self.client.get(url).status_code, 200)
        export_url = reverse('staff_panel:registrations_campaigns_campaign_export', args=[campaign.pk])
        user = get_user_model().objects.create_user(username='staff', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(export_url).status_code, 302)
        user.user_permissions.add(Permission.objects.get(
            content_type__app_label='registrations_campaigns', codename='view_campaign',
        ))
        self.assertEqual(self.client.get(export_url).status_code, 403)
        self.client.force_login(get_user_model().objects.create_superuser(username='manager'))
        response = self.client.get(export_url)
        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(BytesIO(b''.join(response.streaming_content)))
        self.assertEqual(workbook.active['A2'].data_type, 's')
        self.assertEqual(workbook.active['A2'].value, '=1+1')
        self.assertEqual(workbook.active['D2'].value, 'First')
