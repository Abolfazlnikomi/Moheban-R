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
            name='FeedbackCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='عنوان دسته')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
            ],
            options={
                'verbose_name': 'دستهٔ بازخورد',
                'verbose_name_plural': 'دسته\u200cهای بازخورد',
                'ordering': ('position', 'name'),
            },
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('comment', 'نظر'), ('critique', 'انتقاد'), ('suggestion', 'پیشنهاد')], max_length=12, verbose_name='نوع بازخورد')),
                ('title', models.CharField(max_length=150, verbose_name='عنوان')),
                ('body', models.TextField(max_length=4000, verbose_name='متن بازخورد')),
                ('status', models.CharField(choices=[('pending', 'در انتظار بررسی'), ('approved', 'منتشرشده'), ('hidden', 'پنهان')], db_index=True, default='pending', max_length=10, verbose_name='وضعیت انتشار')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='نویسنده')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='feedback_polls.feedbackcategory', verbose_name='دسته')),
            ],
            options={
                'verbose_name': 'بازخورد',
                'verbose_name_plural': 'بازخوردها',
                'ordering': ('-created_at', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=200, verbose_name='سؤال')),
                ('status', models.CharField(choices=[('draft', 'پیش\u200cنویس'), ('open', 'باز'), ('closed', 'پایان\u200cیافته')], default='draft', max_length=8, verbose_name='وضعیت نظرسنجی')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='feedback_polls.feedbackcategory', verbose_name='دسته')),
            ],
            options={
                'verbose_name': 'نظرسنجی',
                'verbose_name_plural': 'نظرسنجی\u200cها',
                'ordering': ('-created_at', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=150, verbose_name='متن گزینه')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='feedback_polls.poll')),
            ],
            options={
                'verbose_name': 'گزینه',
                'verbose_name_plural': 'گزینه\u200cهای نظرسنجی',
                'ordering': ('position', 'pk'),
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='votes', to='feedback_polls.polloption')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='feedback_polls.poll')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('poll', 'user'), name='feedback_one_vote_per_user')],
            },
        ),
    ]
