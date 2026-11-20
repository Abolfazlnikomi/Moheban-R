import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FooterSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='هیئت محبان اهل\u200cبیت علیهم\u200cالسلام', max_length=150, verbose_name='نام هیئت')),
                ('about', models.TextField(blank=True, default='پایگاه فرهنگی و مذهبی محبان', verbose_name='معرفی هیئت')),
                ('goals', models.TextField(blank=True, verbose_name='اهداف')),
                ('activities', models.TextField(blank=True, verbose_name='فعالیت\u200cها')),
                ('contact', models.TextField(blank=True, verbose_name='توضیحات تماس')),
                ('phone', models.CharField(blank=True, max_length=80, verbose_name='شماره تماس')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='ایمیل')),
                ('address', models.TextField(blank=True, verbose_name='نشانی')),
                ('channel_url', models.URLField(blank=True, validators=[django.core.validators.URLValidator(schemes=['https', 'http'])], verbose_name='لینک کانال اصلی')),
                ('instagram_url', models.URLField(blank=True, validators=[django.core.validators.URLValidator(schemes=['https', 'http'])], verbose_name='لینک اینستاگرام')),
            ],
            options={
                'verbose_name': 'اطلاعات فوتر',
                'verbose_name_plural': 'اطلاعات فوتر',
                'constraints': [models.CheckConstraint(condition=models.Q(('pk', 1)), name='site_info_single_footer')],
            },
        ),
        migrations.CreateModel(
            name='SocialLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100, verbose_name='عنوان کانال یا شبکه')),
                ('url', models.URLField(validators=[django.core.validators.URLValidator(schemes=['https', 'http'])], verbose_name='نشانی پیوند')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('footer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='site_info.footersettings')),
            ],
            options={
                'verbose_name': 'پیوند شبکه یا کانال',
                'verbose_name_plural': 'کانال\u200cها و شبکه\u200cهای بیشتر',
                'ordering': ('position', 'pk'),
            },
        ),
    ]
