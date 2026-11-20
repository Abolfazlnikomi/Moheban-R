import announcements.models
import django.db.models.deletion
import reports_media.assets
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('announcements', '0001_initial'),
        ('night_gatherings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='gathering',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='site_announcements', to='night_gatherings.gathering',
                verbose_name='برنامهٔ مرتبط هیئت',
            ),
        ),
        migrations.CreateModel(
            name='AnnouncementImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(
                    upload_to=announcements.models.image_path, validators=[reports_media.assets.validate_cover],
                    verbose_name='تصویر',
                )),
                ('announcement', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='images',
                    to='announcements.announcement',
                )),
            ],
            options={'ordering': ('pk',), 'verbose_name': 'تصویر اطلاعیه', 'verbose_name_plural': 'تصاویر اطلاعیه'},
        ),
    ]
