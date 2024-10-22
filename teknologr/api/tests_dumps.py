from django.contrib.auth.models import User
from members.models import *
from registration.models import *
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

today = timezone.now().date().strftime('%Y-%m-%d')

class BaseClass(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='svakar', password='teknolog')
        self.superuser = User.objects.create_superuser(username='superuser', password='teknolog')

        m = Member.objects.create(
            given_names='Sverker Svakar',
            preferred_name='Svakar',
            surname='von Teknolog',
            street_address='OK22',
            postal_code='12345',
            city='Kouvola',
            country='FI',
            student_id='123456',
            username='vonteks1',
            subscribed_to_modulen=True,
            allow_studentbladet=True,
        )

        ft = FunctionaryType.objects.create(name='Funkkis')
        Functionary.objects.create(member=m, functionarytype=ft, begin_date=today, end_date='2999-01-01')
        d = Decoration.objects.create(name='Hedersmedlem', pk=3)
        DecorationOwnership.objects.create(member=m, decoration=d, acquired='1999-01-01')
        MemberType.objects.create(member=m, type='OM', begin_date='1999-01-01')

        Applicant.objects.create(
            given_names='Siri Svatta',
            preferred_name='Svatta',
            surname='von Teknolog',
            email='svatta@svatta.fi',
            mother_tongue='Svenska',
            birth_date='1999-01-01',
            degree_programme='Teknolog',
            enrolment_year=2010,
        )

    def login_user(self):
        self.client.login(username='svakar', password='teknolog')

    def login_superuser(self):
        self.client.login(username='superuser', password='teknolog')


class DumpsTestCases():
    def get(self):
        return self.client.get(self.path)

    def test_get_for_anonymous_users(self):
        response = self.get()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_for_user(self):
        self.login_user()
        response = self.get()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_for_superuser(self):
        self.login_superuser()
        response = self.get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.response, response.json())

class HTK_Full(BaseClass, DumpsTestCases):
    path = f'/api/dump-htk/'
    response = [{
        'id': 1,
        'name': 'Sverker Svakar von Teknolog',
        'functionaries': [f'Funkkis: {today} > 2999-01-01'],
        'groups': [],
        'membertypes': ['Ordinarie Medlem: 1999-01-01 > None'],
        'decorations': ['Hedersmedlem: 1999-01-01'],
    }]

class HTK_One(BaseClass, DumpsTestCases):
    path = f'/api/dump-htk/1/'
    response = {
        'id': 1,
        'name': 'Sverker Svakar von Teknolog',
        'functionaries': [f'Funkkis: {today} > 2999-01-01'],
        'groups': [],
        'membertypes': ['Ordinarie Medlem: 1999-01-01 > None'],
        'decorations': ['Hedersmedlem: 1999-01-01'],
    }

class Modulen(BaseClass, DumpsTestCases):
    path = f'/api/dump-modulen/'
    response = [{
        'given_names': 'Sverker Svakar',
        'preferred_name': 'Svakar',
        'surname': 'von Teknolog',
        'street_address': 'OK22',
        'postal_code': '12345',
        'city': 'Kouvola',
        'country': 'Finland',
    }]

class Active(BaseClass, DumpsTestCases):
    path = f'/api/dump-active/'
    response = [{
        'position': 'Funkkis',
        'member': 'Sverker Svakar von Teknolog',
    }]

class Arsk(BaseClass, DumpsTestCases):
    path = f'/api/dump-arsk/'
    response = [{
        'name': 'Sverker Svakar',
        'surname': 'von Teknolog',
        'street_address': 'OK22',
        'postal_code': '12345',
        'city': 'Kouvola',
        'country': 'Finland',
        'associations': 'Hedersmedlem,Funkkis',
    }]

class RegEmails(BaseClass, DumpsTestCases):
    path = f'/api/dump-regemails/'
    response = [{
        'name': 'Siri Svatta',
        'surname': 'von Teknolog',
        'preferred_name': 'Svatta',
        'email': 'svatta@svatta.fi',
        'language': 'Svenska',
        'created_at': f'{today}',
        'degree_programme': 'Teknolog',
        'enrolment_year': '2010',
    }]

class Studentbladet(BaseClass, DumpsTestCases):
    path = f'/api/dump-studentbladet/'
    response = [{
        'name': 'Sverker Svakar von Teknolog',
        'street_address': 'OK22',
        'postal_code': '12345',
        'city': 'Kouvola',
        'country': 'FI',
    }]
