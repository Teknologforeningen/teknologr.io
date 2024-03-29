from django.db import models
from django_countries.fields import CountryField
from datetime import datetime


THIS_YEAR = datetime.now().year


class Applicant(models.Model):
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
