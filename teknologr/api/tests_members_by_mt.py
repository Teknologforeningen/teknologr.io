from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from members.models import *
from rest_framework import status
from rest_framework.test import APITestCase

class BaseClass(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='svakar', password='teknolog')
        self.superuser = User.objects.create_superuser(username='superuser', password='teknolog')

    def login_superuser(self):
        self.client.login(username='superuser', password='teknolog')

class TestCases():
    def check_json(self, json, expected_members):
        self.assertEqual([self.map(m) for m in expected_members], json)

    def test_get_for_anonymous_users(self):
        response = self.get('KE')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_for_user(self):
        self.client.login(username='svakar', password='teknolog')
        response = self.get('KE')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_not_found(self):
        self.login_superuser()
        response = self.get('XXX')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_invalid(self):
        self.login_superuser()
        response = self.get('XX')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {'detail': 'invalid membertype'})

    def test_get_only_ongoing(self):
        today = timezone.now().date()
        past = today - timedelta(days=1)
        future = today + timedelta(days=1)

        m1 = Member.objects.create(student_id='111', username='abc1')
        m2 = Member.objects.create(student_id='222', username='abc2')
        m3 = Member.objects.create(student_id='333', username='abc3')
        m4 = Member.objects.create(student_id='444', username='abc4')

        MemberType.objects.create(member=m1, type='KE')
        MemberType.objects.create(member=m2, type='KE', end_date=today)
        MemberType.objects.create(member=m3, type='KE', end_date=past)
        MemberType.objects.create(member=m4, type='KE', end_date=future)

        self.login_superuser()
        response = self.get('KE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1), self.map(m2), self.map(m4)])

    def test_null_values(self):
        m1 = Member.objects.create(student_id='123456', username='abc1')
        m2 = Member.objects.create()

        MemberType.objects.create(member=m1, type='KE')
        MemberType.objects.create(member=m2, type='KE')

        self.login_superuser()

        response = self.get('KE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)] + [None])

        response = self.get('KE', True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)])

    def test_doubles(self):
        m1 = Member.objects.create(student_id='123456', username='abc1')

        MemberType.objects.create(member=m1, type='KE')
        MemberType.objects.create(member=m1, type='KE')
        MemberType.objects.create(member=m1, type='KE')

        self.login_superuser()
        response = self.get('KE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)])

    def test_OM(self):
        m1 = Member.objects.create(student_id='111', username='abc1')
        m2 = Member.objects.create(student_id='222', username='abc2')
        m3 = Member.objects.create(student_id='333', username='abc3', graduated=True)
        m4 = Member.objects.create(student_id='444', username='abc4', graduated_year=2023)
        m5 = Member.objects.create(student_id='555', username='abc5')
        m6 = Member.objects.create(student_id='666', username='abc6')
        m7 = Member.objects.create(student_id='777', username='abc7')

        MemberType.objects.create(member=m1, type='OM')

        # Ended
        MemberType.objects.create(member=m2, type='OM', end_date="2010-01-01")

        # Graduated
        MemberType.objects.create(member=m3, type='OM')

        # Graduated year
        MemberType.objects.create(member=m4, type='OM')

        # Has 'ST' MemberType
        MemberType.objects.create(member=m5, type='OM')
        MemberType.objects.create(member=m5, type='ST')

        # Has 'FG' MemberType
        MemberType.objects.create(member=m6, type='OM')
        MemberType.objects.create(member=m6, type='FG')

        # Has 'EM' MemberType
        MemberType.objects.create(member=m7, type='OM')
        MemberType.objects.create(member=m7, type='EM')

        self.login_superuser()
        response = self.get('OM')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)])

    def test_JS(self):
        m1 = Member.objects.create(student_id='111', username='abc1')
        m2 = Member.objects.create(student_id='222', username='abc2')
        m3 = Member.objects.create(student_id='333', username='abc3', graduated=True)
        m4 = Member.objects.create(student_id='444', username='abc4', graduated_year=2023)
        m5 = Member.objects.create(student_id='555', username='abc5')
        m6 = Member.objects.create(student_id='666', username='abc6')
        m7 = Member.objects.create(student_id='777', username='abc7')

        MemberType.objects.create(member=m1, type='JS')

        # Ended
        MemberType.objects.create(member=m2, type='JS', end_date="2010-01-01")

        # Graduated
        MemberType.objects.create(member=m3, type='JS')

        # Graduated year
        MemberType.objects.create(member=m4, type='JS')

        # Has 'ST' MemberType
        MemberType.objects.create(member=m5, type='JS')
        MemberType.objects.create(member=m5, type='ST')

        # Has 'FG' MemberType
        MemberType.objects.create(member=m6, type='JS')
        MemberType.objects.create(member=m6, type='FG')

        # Has 'EM' MemberType
        MemberType.objects.create(member=m7, type='JS')
        MemberType.objects.create(member=m7, type='EM')

        self.login_superuser()
        response = self.get('JS')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)])

    def test_ST(self):
        m1 = Member.objects.create(student_id='111', username='abc1')
        m2 = Member.objects.create(student_id='222', username='abc2')
        m3 = Member.objects.create(student_id='333', username='abc3')

        MemberType.objects.create(member=m1, type='ST')

        # Ended
        MemberType.objects.create(member=m2, type='ST', end_date="2010-01-01")

        # Has 'EM' MemberType
        MemberType.objects.create(member=m3, type='ST')
        MemberType.objects.create(member=m3, type='EM')

        self.login_superuser()
        response = self.get('ST')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)])

    def test_PH(self):
        m1 = Member.objects.create(student_id='111', username='abc1')
        m2 = Member.objects.create(student_id='222', username='abc2')
        m3 = Member.objects.create(student_id='333', username='abc3', graduated=True)
        m4 = Member.objects.create(student_id='444', username='abc4', graduated_year=2023)
        m5 = Member.objects.create(student_id='555', username='abc5')
        m6 = Member.objects.create(student_id='666', username='abc6')
        m7 = Member.objects.create(student_id='777', username='abc7')

        MemberType.objects.create(member=m1, type='PH')

        # Ended
        MemberType.objects.create(member=m2, type='PH', end_date="2010-01-01")

        # Graduated
        MemberType.objects.create(member=m3, type='PH')

        # Graduated year
        MemberType.objects.create(member=m4, type='PH')

        # Has 'OM' MemberType
        MemberType.objects.create(member=m5, type='PH')
        MemberType.objects.create(member=m5, type='OM')

        # Has 'ST' MemberType
        MemberType.objects.create(member=m6, type='PH')
        MemberType.objects.create(member=m6, type='ST')

        # Has 'EM' MemberType
        MemberType.objects.create(member=m7, type='PH')
        MemberType.objects.create(member=m7, type='EM')

        self.login_superuser()
        response = self.get('PH')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [self.map(m1)])

class StudynumbersByMTTests(BaseClass, TestCases):
    def get(self, type, skip_null=False):
        url = f'/api/membersByMemberType/{type}/'
        if skip_null:
            url += "?skip_null=True"
        return self.client.get(url)

    def map(self, member):
        return member.student_id


class UsernamesByMTTests(BaseClass, TestCases):
    def get(self, type, skip_null=False):
        url = f'/api/membersByMemberType/{type}/usernames'
        if skip_null:
            url += "?skip_null=True"
        return self.client.get(url)

    def map(self, member):
        return member.username
