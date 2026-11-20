from django import forms

from .models import Experience, Scope, Subgroup


class ExperienceForm(forms.ModelForm):
    scope = forms.ModelChoiceField(label='موضوع اصلی', queryset=Scope.objects.none())

    class Meta:
        model = Experience
        fields = ('scope', 'subgroup', 'title', 'body')

    def __init__(self, *args, scopes, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scope'].queryset = scopes
        self.fields['subgroup'].queryset = Subgroup.objects.filter(scope__in=scopes).select_related('scope')

    def clean(self):
        data = super().clean()
        scope, subgroup = data.get('scope'), data.get('subgroup')
        if scope is not None and subgroup is not None and subgroup.scope_id != scope.pk:
            self.add_error('subgroup', 'زیرگروه باید متعلق به موضوع اصلی انتخاب‌شده باشد.')
        return data
