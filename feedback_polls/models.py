from django.conf import settings
from django.db import models


class FeedbackCategory(models.Model):
    name = models.CharField('عنوان دسته', max_length=100, unique=True)
    position = models.PositiveIntegerField('ترتیب نمایش', default=0)

    class Meta:
        ordering = ('position', 'name')
        verbose_name = 'دستهٔ بازخورد'
        verbose_name_plural = 'دسته‌های بازخورد'

    def __str__(self):
        return self.name


class Feedback(models.Model):
    class Kind(models.TextChoices):
        COMMENT = 'comment', 'نظر'
        CRITIQUE = 'critique', 'انتقاد'
        SUGGESTION = 'suggestion', 'پیشنهاد'

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار بررسی'
        APPROVED = 'approved', 'منتشرشده'
        HIDDEN = 'hidden', 'پنهان'

    category = models.ForeignKey(FeedbackCategory, models.PROTECT, verbose_name='دسته')
    kind = models.CharField('نوع بازخورد', max_length=12, choices=Kind.choices)
    title = models.CharField('عنوان', max_length=150)
    body = models.TextField('متن بازخورد', max_length=4000)
    status = models.CharField('وضعیت انتشار', max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True, verbose_name='نویسنده')
    created_at = models.DateTimeField('زمان ثبت', auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-pk')
        verbose_name = 'بازخورد'
        verbose_name_plural = 'بازخوردها'

    def __str__(self):
        return self.title


class Poll(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'پیش‌نویس'
        OPEN = 'open', 'باز'
        CLOSED = 'closed', 'پایان‌یافته'

    question = models.CharField('سؤال', max_length=200)
    category = models.ForeignKey(FeedbackCategory, models.PROTECT, verbose_name='دسته')
    status = models.CharField('وضعیت نظرسنجی', max_length=8, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField('زمان ایجاد', auto_now_add=True)

    class Meta:
        ordering = ('-created_at', '-pk')
        verbose_name = 'نظرسنجی'
        verbose_name_plural = 'نظرسنجی‌ها'

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, models.CASCADE, related_name='options')
    text = models.CharField('متن گزینه', max_length=150)
    position = models.PositiveIntegerField('ترتیب نمایش', default=0)

    class Meta:
        ordering = ('position', 'pk')
        verbose_name = 'گزینه'
        verbose_name_plural = 'گزینه‌های نظرسنجی'

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, models.CASCADE)
    option = models.ForeignKey(PollOption, models.RESTRICT, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('poll', 'user'), name='feedback_one_vote_per_user')]
