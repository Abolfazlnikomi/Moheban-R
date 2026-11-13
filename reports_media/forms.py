from django import forms

from .models import Category, Event, MediaPost

DATE_INPUT = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class ArchiveFilters(forms.Form):
    q = forms.CharField(label='جست‌وجو', required=False, max_length=150,
                        widget=forms.TextInput(attrs={'placeholder': 'عنوان، توضیحات یا برچسب'}))
    date_from = forms.DateField(label='تاریخ مراسم از', required=False, widget=DATE_INPUT, input_formats=['%Y-%m-%d'])
    date_to = forms.DateField(label='تاریخ مراسم تا', required=False, widget=DATE_INPUT, input_formats=['%Y-%m-%d'])
    kind = forms.ChoiceField(label='نوع محتوا', required=False, choices=[('', 'همه'), *MediaPost.Kind.choices])
    category = forms.ModelChoiceField(label='دسته‌بندی', queryset=Category.objects.all(), required=False, empty_label='همه')
    event = forms.ModelChoiceField(label='مراسم', queryset=Event.objects.all(), required=False, empty_label='همه')
    sort = forms.ChoiceField(label='مرتب‌سازی', required=False, choices=[
        ('newest', 'جدیدترین'), ('event', 'تاریخ مراسم'), ('popular', 'پربازدیدترین'),
    ])

    def clean(self):
        data = super().clean()
        start, end = data.get('date_from'), data.get('date_to')
        if start and end and start > end:
            self.add_error('date_to', 'تاریخ پایان نباید قبل از تاریخ شروع باشد.')
        return data
