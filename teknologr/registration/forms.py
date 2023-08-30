from django import forms
from django.utils.translation import gettext as _
from registration.models import Applicant
from registration.labels import MEMBERSHIP_FORM_LABELS
from members.programmes import DEGREE_PROGRAMME_CHOICES
from datetime import datetime
from members.models import Member
import re


def format_programmes():
    return sorted([
        ('{}_{}'.format(school, programme), '{} - {}'.format(school, programme))
        for school, programmes in DEGREE_PROGRAMME_CHOICES.items()
        for programme in programmes
    ])


class DateInput(forms.DateInput):
    input_type = 'date'


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = '__all__'
        labels = MEMBERSHIP_FORM_LABELS
        widgets = {
            'birth_date': DateInput(),
        }

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self._set_programme_choices()
        self._set_attributes()
        # Specify unrequired fields
        self.fields['preferred_name'].required = False
        self.fields['mother_tongue'].required = False
        self.fields['username'].required = False
        # Specify required fields
        self.fields['country'].required = True

    def _set_attributes(self):
        for fname, f in self.fields.items():
            f.widget.attrs['autocomplete'] = 'off'

    def _set_programme_choices(self):
        degree_programme_label = MEMBERSHIP_FORM_LABELS['degree_programme_options']

        programmes = [('', 'SKOLA - LINJE')]  # Default setting
        programmes.extend(format_programmes())
        programmes.append(('extra', 'ÖVRIG'))

        self.fields['degree_programme_options'] = forms.ChoiceField(
            choices=programmes,
            label=degree_programme_label,
            widget=forms.widgets.Select(attrs={'id': 'id_degree_programme_options'}))

        self.fields['degree_programme'] = forms.CharField(
            label=MEMBERSHIP_FORM_LABELS['degree_programme'],
            widget=forms.widgets.TextInput(attrs={'placeholder': degree_programme_label}))

    def clean(self):
        cleaned_data = super().clean()

        preferred_name = cleaned_data.get('preferred_name')
        if preferred_name and (' ' in preferred_name or preferred_name not in cleaned_data.get('given_names')):
            self.add_error('preferred_name', 'Tilltalsnamnet måste vara ett av förnamnen')

        enrolment_year = cleaned_data.get('enrolment_year')
        if enrolment_year and enrolment_year > datetime.now().year:
            self.add_error('enrolment_year', 'Inskrivningsåret kan inte vara i framtiden')

        # Check if the username is taken if one was provided in the application
        username = cleaned_data.get('username')
        if username:
            if Member.objects.filter(username=username).exists():
                self.add_error('username', 'Användarnamnet är inte ledigt')

            # Our convetion has always been that LDAP username is the one that is used at the university, which only has small letters and numbers
            if not re.search(r'^[a-z0-9]+$', username):
                self.add_error('username', 'Användarnamnet kan endast innehålla små bokstäver och siffror, som vid universitetet')
