from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from datetime import datetime
import re

def in_range(value, a, b):
    if value is None:
        return True
    if a is not None and value < a:
        return False
    if b is not None and value > b:
        return False
    return True

class CommonValidators:
    '''
    Form validators for Members and Applicants.
    '''

    # XXX: Validate student id?

    def clean_given_names(self):
        given_names = self.cleaned_data.get('given_names')
        regex = re.compile('^[a-zA-Z -]*$')
        if not regex.match(given_names):
            raise ValidationError('Ogiltigt förnamn')
        return given_names

    def clean_surname(self):
        surname = self.cleaned_data.get('surname')
        regex = re.compile('^[a-zA-Z -]*$')
        if not regex.match(surname):
            raise ValidationError('Ogiltigt efternamn')
        return surname

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return ''
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError('Ogiltig e-postadress')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return ''
        regex = re.compile('^\+?[0-9][0-9- ]*[0-9]$')
        if not regex.match(phone) or '--' in phone:
            raise ValidationError('Ogiltigt telefonnummer')
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        # XXX: What would be a suitable cutoff?
        if birth_date and not in_range(birth_date.year, 1000, datetime.now().year - 10):
            raise ValidationError('Ogiltigt födelsedatum')
        return birth_date

    def clean(self):
        street_address = self.cleaned_data.get('street_address')
        postal_code = self.cleaned_data.get('postal_code')
        city = self.cleaned_data.get('city')

        valid_address = all([street_address, postal_code, city])
        # Country is assumed to be Finland by default, so the address can be valid without it
        # XXX: Validate the address for real?

        if not valid_address:
            if any([street_address, postal_code, city]):
                self.add_error('street_address', 'En giltig adress kväver gatuadress, postnummer och postanstalt')
            else:
                self.cleaned_data['country'] = ''

            if self.cleaned_data.get('subscribed_to_modulen'):
                self.add_error('subscribed_to_modulen', 'Prenumeration av Modulen kräver en giltig adress')

            if self.cleaned_data.get('allow_studentbladet'):
                self.add_error('allow_studentbladet', 'Prenumeration av Studentbladet kräver en giltig adress')

        preferred_name = self.cleaned_data.get('preferred_name')
        if preferred_name:
            # If given_names is "A-B C", I want A-B, A, B and C to be valid as preferred_name
            given_names = self.cleaned_data.get('given_names') or (self.instance.given_names if self.instance else '')
            given_names_a = given_names.split(' ')
            given_names_b = re.split(r'[- ]+', given_names)
            if ' ' in preferred_name or (preferred_name not in given_names_a and preferred_name not in given_names_b):
                self.add_error('preferred_name', 'Tilltalsnamnet måste vara ett av förnamnen')

        graduated_year = self.cleaned_data.get('graduated_year')
        if graduated_year:
            # XXX: This change does not show up until page reload for some reason
            self.cleaned_data['graduated'] = True

        # Some validation of various years, for the sake of minimizing mistakes
        birth_date = self.cleaned_data.get('birth_date') or (self.instance.birth_date if self.instance else None)
        minimum = birth_date.year + 10 if birth_date else 1000
        maximum = datetime.now().year

        enrolment_year = self.cleaned_data.get('enrolment_year')
        if not in_range(enrolment_year, minimum, maximum):
            self.add_error('enrolment_year', f'Inskrivningsåret kan inte vara i framtiden eller för snabbt efter födelseåret')

        enrolment_year = enrolment_year or (self.instance.enrolment_year if self.instance else None)
        if not in_range(graduated_year, enrolment_year or minimum, maximum):
            self.add_error('graduated_year', 'Utexamineringsåret kan inte vara i framtiden och måste vara efter födelseåret och inskrivningsåret')
