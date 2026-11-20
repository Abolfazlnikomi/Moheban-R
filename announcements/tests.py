from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from dorm_heiat.models import Unit, UnitType
from night_gatherings.models import Gathering

from .models import Announcement


def uploaded_image(name):
    buffer = BytesIO()
    Image.new('RGB', (16, 16), 'green').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class AnnouncementTests(TestCase):
    def test_public_archive_lists_older_notices_but_not_drafts_or_scheduled_notices(self):
        now = timezone.now()
        Announcement.objects.create(title='Old notice', published=True, published_at=now - timedelta(days=30))
        for index in range(12):
            Announcement.objects.create(title=f'Recent notice {index}', published=True, published_at=now)
        Announcement.objects.create(title='Hidden draft')
        Announcement.objects.create(title='Scheduled notice', published=True, published_at=now + timedelta(days=1))
        self.assertNotContains(self.client.get(reverse('announcements:list')), 'Old notice')
        archive = reverse('announcements:archive')
        older_page = self.client.get(archive, {'page': 2})
        self.assertContains(older_page, 'Old notice')
        self.assertNotContains(older_page, 'Hidden draft')
        self.assertNotContains(self.client.get(archive), 'Scheduled notice')

    def test_delegated_editor_can_upload_multiple_images_and_link_notice(self):
        editor = User.objects.create(username='editor', is_staff=True)
        self.client.force_login(editor)
        add_url = reverse('staff_panel:announcements_announcement_add')
        self.assertEqual(self.client.get(add_url).status_code, 403)
        editor.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='announcements',
            codename__in=('add_announcement', 'change_announcement', 'delete_announcement'),
        ))
        unit = Unit.objects.create(name='Dormitory', unit_type=UnitType.objects.create(name='Dorm'))
        gathering = Gathering.objects.create(title='Gathering', starts_at=timezone.now(), status=Gathering.Status.PUBLISHED)
        gathering.units.add(unit)
        data = {
            'title': 'Schedule update', 'description': 'New time details', 'published_at': timezone.now().isoformat(),
            'gathering': gathering.pk, 'is_public': 'on', 'units': [unit.pk],
        }
        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            self.assertContains(self.client.get(add_url), 'multiple')
            invalid = self.client.post(add_url, {**data, 'new_images': [
                uploaded_image('first.png'), SimpleUploadedFile('invalid.png', b'not an image'),
            ]})
            self.assertIn('new_images', invalid.context['form'].errors)
            self.assertFalse(Announcement.objects.exists())
            result = self.client.post(add_url, {**data, 'new_images': [
                uploaded_image('first.png'), uploaded_image('second.png'),
            ]})
            self.assertEqual(result.status_code, 302)
            notice = Announcement.objects.get()
            self.assertEqual(notice.gathering, gathering)
            self.assertEqual(list(notice.units.all()), [unit])
            first, second = notice.images.all()
            image_url = reverse('announcements:image', args=[second.pk])
            preview = self.client.get(image_url)
            self.assertEqual(preview.status_code, 200)
            preview.close()
            self.client.logout()
            self.assertEqual(self.client.get(image_url).status_code, 404)
            self.client.force_login(editor)
            edit_url = reverse('staff_panel:announcements_announcement_change', args=[notice.pk])
            self.assertContains(self.client.get(edit_url), 'remove_images')
            updated = self.client.post(edit_url, {**data, 'published': 'on', 'remove_images': [first.pk]})
            self.assertEqual(updated.status_code, 302)
            self.assertEqual(list(notice.images.all()), [second])
            self.client.logout()
            self.assertContains(self.client.get(notice.get_absolute_url()), image_url)
            self.assertContains(self.client.get(gathering.get_absolute_url()), notice.get_absolute_url())
            public_image = self.client.get(image_url)
            self.assertEqual(public_image.headers['Content-Type'], 'image/png')
            public_image.close()
            self.client.force_login(editor)
            delete_url = reverse('staff_panel:announcements_announcement_delete', args=[notice.pk])
            self.assertEqual(self.client.post(delete_url).status_code, 302)
            self.assertEqual(self.client.get(image_url).status_code, 404)

    def test_superuser_can_open_native_admin_form(self):
        self.client.force_login(User.objects.create_superuser(username='administrator'))
        self.assertContains(self.client.get(reverse('admin:announcements_announcement_add')), 'multiple')
