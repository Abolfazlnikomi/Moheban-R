import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Scope',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='نام حوزه')),
            ],
            options={
                'verbose_name': 'حوزهٔ تجربه\u200cنگاری',
                'verbose_name_plural': 'حوزه\u200cهای تجربه\u200cنگاری',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ExperienceAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False, verbose_name='دسترسی تجربه\u200cنگاری فعال باشد')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='experience_access', to=settings.AUTH_USER_MODEL)),
                ('scopes', models.ManyToManyField(blank=True, to='experience_writing.scope', verbose_name='حوزه\u200cهای مجاز')),
            ],
            options={
                'verbose_name': 'دسترسی تجربه\u200cنگاری',
                'verbose_name_plural': 'دسترسی تجربه\u200cنگاری',
            },
        ),
        migrations.CreateModel(
            name='Subgroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='نام زیرگروه')),
                ('scope', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subgroups', to='experience_writing.scope', verbose_name='حوزه')),
            ],
            options={
                'verbose_name': 'زیرگروه تجربه\u200cنگاری',
                'verbose_name_plural': 'زیرگروه\u200cهای تجربه\u200cنگاری',
                'ordering': ('scope__name', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Experience',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان یا توضیح کوتاه')),
                ('body', models.TextField(verbose_name='متن اصلی تجربه')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='written_experiences', to=settings.AUTH_USER_MODEL, verbose_name='نویسنده')),
                ('subgroup', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='experiences', to='experience_writing.subgroup', verbose_name='زیرگروه')),
            ],
            options={
                'verbose_name': 'تجربه',
                'verbose_name_plural': 'تجربه\u200cها',
                'ordering': ('-recorded_at', '-pk'),
            },
        ),
        migrations.AddConstraint(
            model_name='subgroup',
            constraint=models.UniqueConstraint(fields=('scope', 'name'), name='experience_unique_subgroup'),
        ),
    ]
