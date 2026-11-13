import re
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import CampaignEntry, CampaignField, VolunteerApplication, VolunteerSection

DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def normalize_phone(value):
    value = re.sub(r'[\s-]+', '', value.translate(DIGITS))
    value = re.sub(r'^(?:\+98|0098)', '0', value)
    if not re.fullmatch(r'09[0-9]{9}', value):
        raise ValidationError('شمارهٔ موبایل معتبر وارد کنید؛ مانند 09123456789.')
    return value


class PhoneField(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(max_length=32, widget=forms.TextInput(attrs={'type': 'tel', 'dir': 'ltr'}), **kwargs)

    def clean(self, value):
        return normalize_phone(super().clean(value))


class VolunteerForm(forms.ModelForm):
    phone = PhoneField(label='شماره تماس')
    national_id = forms.CharField(label='کد ملی', max_length=10, min_length=10,
                                  widget=forms.TextInput(attrs={'inputmode': 'numeric', 'dir': 'ltr'}))
    section = forms.ModelChoiceField(label='بخش موردعلاقه', queryset=VolunteerSection.objects.filter(active=True))
    birth_date = forms.DateField(label='تاریخ تولد', required=False, input_formats=['%Y-%m-%d'],
                                 widget=forms.DateInput(attrs={'type': 'date'}), help_text='تاریخ میلادی.')

    class Meta:
        model = VolunteerApplication
        fields = ('first_name', 'last_name', 'phone', 'national_id', 'birth_date', 'skills', 'section', 'availability')

    def __init__(self, *args, settings, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('birth_date', 'skills', 'availability'):
            self.fields[name].required = getattr(settings, f'require_{name}')

    def clean_national_id(self):
        value = self.cleaned_data['national_id'].translate(DIGITS)
        if re.fullmatch(r'[0-9]{10}', value) and len(set(value)) > 1:
            remainder = sum(int(digit) * weight for digit, weight in zip(value[:9], range(10, 1, -1))) % 11
            if int(value[-1]) == (remainder if remainder < 2 else 11 - remainder):
                return value
        raise ValidationError('کد ملی معتبر وارد کنید.')

    def clean_birth_date(self):
        value = self.cleaned_data['birth_date']
        if value and (value > date.today() or value.year < 1900):
            raise ValidationError('تاریخ تولد معتبر وارد کنید.')
        return value


class CampaignEntryForm(forms.ModelForm):
    phone = PhoneField(label='شماره تماس')

    class Meta:
        model = CampaignEntry
        fields = ('full_name', 'phone')

    def __init__(self, *args, campaign, **kwargs):
        super().__init__(*args, **kwargs)
        self.campaign = campaign
        self.definitions = list(campaign.fields.all())
        for definition in self.definitions:
            options = {'label': definition.label, 'required': definition.required}
            if definition.kind in (CampaignField.Kind.CHOICE, CampaignField.Kind.YES_NO):
                values = definition.option_values() if definition.kind == CampaignField.Kind.CHOICE else ['بله', 'خیر']
                form_field = forms.ChoiceField(choices=[('', 'انتخاب کنید'), *((value, value) for value in values)], **options)
            elif definition.kind == CampaignField.Kind.LONG_TEXT:
                form_field = forms.CharField(max_length=2000, widget=forms.Textarea(attrs={'rows': 4}), **options)
            else:
                form_field = forms.CharField(max_length=250, **options)
            self.fields[f'custom_{definition.pk}'] = form_field

    def save(self, commit=True):
        entry = super().save(commit=False)
        entry.campaign = self.campaign
        entry.answers = [
            {'id': definition.pk, 'label': definition.label, 'value': self.cleaned_data[f'custom_{definition.pk}']}
            for definition in self.definitions
        ]
        if commit:
            entry.save()
        return entry

