from django.contrib import admin

from .models import Feedback, FeedbackCategory, Poll, PollOption


@admin.register(FeedbackCategory)
class FeedbackCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')
    list_editable = ('position',)
    search_fields = ('name',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'kind')
    search_fields = ('title', 'body')
    readonly_fields = ('author', 'created_at')
    actions = ('approve', 'hide')

    @admin.action(description='انتشار بازخوردهای انتخاب‌شده', permissions=['change'])
    def approve(self, request, queryset):
        queryset.update(status=Feedback.Status.APPROVED)

    @admin.action(description='پنهان کردن بازخوردهای انتخاب‌شده', permissions=['change'])
    def hide(self, request, queryset):
        queryset.update(status=Feedback.Status.HIDDEN)


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('question',)
    inlines = (PollOptionInline,)
