from django import forms
from .models import LiveStream


class LiveStreamForm(forms.ModelForm):
    class Meta:
        model = LiveStream
        fields = (
            'title',
            'description',
            'embed_url',
            'is_active',
        )

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان پخش زنده',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
            'embed_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'لینک Embed آپارات',
                'dir': 'ltr',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }