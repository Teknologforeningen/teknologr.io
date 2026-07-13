from django.db import models
from django.db.models import Q
from django.utils.html import format_html
from django_countries.fields import CountryField
from datetime import datetime
from locale import strxfrm


THIS_YEAR = datetime.now().year

class ApplicantManager(models.Manager):
    def search_by_name(self, queries):
        if not queries:
            return []

        queries = [q.lower() for q in queries]
        filters = [(
            Q(given_names__icontains=q) |
            Q(preferred_name__icontains=q) |
            Q(surname__icontains=q) |
            Q(email__icontains=q)
        ) for q in queries]

        return list(self.filter(*filters))

class Applicant(models.Model):
    objects = ApplicantManager()

    # NAMES
    surname = models.CharField(max_length=100)
    given_names = models.CharField(max_length=64)
    preferred_name = models.CharField(max_length=32, default='')
    # ADDRESS
    street_address = models.CharField(max_length=64)
    postal_code = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    # Country
    country = CountryField(blank=True, null=False, default='FI')
    # CONTACT INFO
    phone = models.CharField(max_length=128)
    email = models.EmailField(max_length=64)
    # DATE OF BIRTH
    birth_date = models.DateField()
    # STUDIES
    student_id = models.CharField(max_length=10)
    degree_programme = models.CharField(max_length=256)
    enrolment_year = models.IntegerField(choices=[(y, y) for y in range(1872, THIS_YEAR+1)], default=THIS_YEAR)
    # LDAP username
    username = models.CharField(max_length=16, blank=False, null=True)
    # MEMBERSHIP MOTIVATION
    motivation = models.TextField(max_length=2048, default='')
    # CONSENTS
    subscribed_to_modulen = models.BooleanField(default=False)
    allow_publish_info = models.BooleanField(default=False)
    allow_studentbladet = models.BooleanField(default=False)
    # MOTHER TONGUE
    mother_tongue = models.CharField(max_length=64, default='')

    # FORM METADATA
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return f'{self.given_names} {self.surname}'

    @property
    def name(self):
        return self.full_name

    def __str__(self):
        return '{} {}: {}'.format(self.given_names, self.surname, self.student_id)

    def get_given_names(self):
        return self.given_names.split() if self.given_names else ['']

    def get_preferred_name(self):
        return self.preferred_name or self.get_given_names()[0]

    def get_full_name_HTML(self):
        preferred_name = self.get_preferred_name()
        given_names_HTML = self.given_names.replace(preferred_name, f"<u>{preferred_name}</u>", 1) if preferred_name else self.given_names
        return format_html(f'{given_names_HTML} {self.surname}')

    def get_full_name_for_sorting(self):
        return f'{self.surname}, {self.given_names}'

    @classmethod
    def order_by(cls, applicant_list, by, reverse=False):
        if by == 'name':
            key = lambda a: strxfrm(a.get_full_name_for_sorting())
        else:
            return
        applicant_list.sort(key=key, reverse=reverse)
