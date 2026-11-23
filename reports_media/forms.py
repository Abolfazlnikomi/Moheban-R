from django import forms
from dorm_heiat.models import Unit
from .models import Category, Event, MediaPost

DATE_INPUT = forms.DateInput(
    attrs={'type': 'date', 'class': 'filter-input'},
    format='%Y-%m-%d'
)

class ArchiveFilters(forms.Form):
    q = forms.CharField(
        label='جست‌وجو در محتوا',
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'عنوان، توضیحات یا برچسب رویداد...',
            'class': 'filter-input'
        })
    )
    date_from = forms.DateField(
        label='از تاریخ مراسم',
        required=False,
        widget=DATE_INPUT,
        input_formats=['%Y-%m-%d']
    )
    date_to = forms.DateField(
        label='تا تاریخ مراسم',
        required=False,
        widget=DATE_INPUT,
        input_formats=['%Y-%m-%d']
    )
    kind = forms.ChoiceField(
        label='نوع رسانه',
        required=False,
        choices=[('', 'همه انواع محتوا'), *MediaPost.Kind.choices],
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    category = forms.ModelChoiceField(
        label='دسته‌بندی',
        queryset=Category.objects.all(),
        required=False,
        empty_label='همه دسته‌بندی‌ها',
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    event = forms.ModelChoiceField(
        label='مراسم / رویداد',
        queryset=Event.objects.all(),
        required=False,
        empty_label='همه مراسم‌ها',
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    unit = forms.ModelChoiceField(
        label='واحد برگزارکننده',
        queryset=Unit.objects.all(),
        required=False,
        empty_label='همه واحدها',
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    sort = forms.ChoiceField(
        label='مرتب‌سازی',
        required=False,
        choices=[
            ('newest', 'جدیدترین محتوا'),
            ('event', 'تاریخ برگزاری مراسم'),
            ('popular', 'پربازدیدترین'),
        ],
        widget=forms.Select(attrs={'class': 'filter-select'})
    )

    def clean(self):
        data = super().clean()
        start, end = data.get('date_from'), data.get('date_to')
        if start and end and start > end:
            self.add_error('date_to', 'تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.')
        return data
