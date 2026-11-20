from django import forms

from .models import Feedback, FeedbackCategory, PollOption


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('category', 'kind', 'title', 'body')
        widgets = {'body': forms.Textarea(attrs={'rows': 5})}


class ModerationFilter(forms.Form):
    category = forms.ModelChoiceField(label='دسته', queryset=FeedbackCategory.objects.all(),
                                      empty_label='همهٔ دسته‌ها', required=False)
    status = forms.ChoiceField(label='وضعیت انتشار', choices=[('', 'همهٔ وضعیت‌ها'), *Feedback.Status.choices],
                               required=False)
    sort = forms.ChoiceField(label='ترتیب', choices=[('', 'جدیدترین'), ('oldest', 'قدیمی‌ترین')], required=False)

    def apply(self, entries):
        if self.is_valid():
            if self.cleaned_data['category']:
                entries = entries.filter(category=self.cleaned_data['category'])
            if self.cleaned_data['status']:
                entries = entries.filter(status=self.cleaned_data['status'])
            if self.cleaned_data['sort'] == 'oldest':
                entries = entries.order_by('created_at', 'pk')
        return entries


class VoteForm(forms.Form):
    option = forms.ModelChoiceField(label='گزینه‌ها', queryset=PollOption.objects.none(), widget=forms.RadioSelect,
                                   empty_label=None)

    def __init__(self, *args, poll, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['option'].queryset = poll.options.all()
