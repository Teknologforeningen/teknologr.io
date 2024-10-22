from django.contrib.auth.models import User, Group
from members.models import *
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import date

'''
This file tests the filtering on the Members API.
'''

class BaseAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='svakar', password='teknolog')
        self.superuser = User.objects.create_superuser(username='superuser', password='teknolog')

        # This Member should almost never be found
        Member.objects.create(
            given_names='Dummy',
            surname='von Dummy',
            street_address='Dummyvägen 42',
            city='Dummystaden',
            country='SE',
            email='dummy@dummy.net',
            degree_programme='Dummylinjen',
            enrolment_year=1999,
            graduated=False,
            graduated_year=None,
            birth_date=date(1999, 1, 1),
            student_id='12345L',
            dead=False,
            subscribed_to_modulen=False,
            allow_studentbladet=False,
            allow_publish_info=True,
            comment='Dummy',
            username='dummyd1',
            bill_code=42,
        )

    def login_user(self):
        self.client.login(username='svakar', password='teknolog')

    def login_superuser(self):
        self.client.login(username='superuser', password='teknolog')

class TestCases():
    def filter(self):
        return self.client.get(f'/api/members/?{self.query}')

    def test_filter_for_anonymous_users(self):
        response = self.filter()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_filter_for_user(self):
        self.login_user()
        response = self.filter()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.json()['count'], self.n_normal)

    def test_filter_for_superuser(self):
        self.login_superuser()
        response = self.filter()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.json()['count'], self.n_staff)


class MemberFilterSingleNameTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'name=Svakar'
        self.n_normal = 3
        self.n_staff = 5

        # Should be found by all
        Member.objects.create(
            # In preferred name, even if hidden and alive
            given_names='Sverker Svakar',
            preferred_name='Svakar',
            surname='von Teknolog',
            allow_publish_info=False,
            dead=False,
        )
        Member.objects.create(
            # In surname, even if hidden and alive
            given_names='Sverker',
            surname='von Svakar',
            allow_publish_info=False,
            dead=False,
        )
        Member.objects.create(
            # In given names for public Member
            given_names='Sverker Svakar',
            surname='von Teknolog',
            allow_publish_info=True,
            dead=False,
        )
        Member.objects.create(
            # In given names but dead
            given_names='Sverker Svakar',
            surname='von Teknolog',
            allow_publish_info=False,
            dead=True,
        )

        # Should only be found by staff
        Member.objects.create(
            # No preferred name on hidden Member
            given_names='Sverker Svakar',
            surname='von Teknolog',
            allow_publish_info=False,
            dead=False,
        )


class MemberFilterMultipleNamesTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'name=Svakar+von+Teknolog'
        self.n_normal = 3
        self.n_staff = 4

        # Should be found by all
        Member.objects.create(
            # Part of preferred and surname name, even if hidden and dead
            given_names='Sverker Svakar',
            preferred_name='Svakar',
            surname='von Teknolog',
            allow_publish_info=False,
            dead=True,
        )
        Member.objects.create(
            # Part of given names and surname for public Member
            given_names='Sverker Svakar',
            surname='von Teknolog',
            allow_publish_info=True,
            dead=False,
        )

        # Should only be found by staff
        Member.objects.create(
            # Part of given names and surname for hidden Member
            given_names='Sverker Svakar',
            surname='von Teknolog',
            allow_publish_info=False,
            dead=False,
        )

        # Should not be found
        Member.objects.create(
            given_names='Sverker Svakar',
            preferred_name='Sverker',
            surname='von Teknolog',
            allow_publish_info=True,
        )
        Member.objects.create(
            given_names='Sverker Svakar',
            preferred_name='Svakar',
            surname='Teknolog',
            allow_publish_info=True,
        )
        Member.objects.create(
            given_names='Sverker Svakar',
            preferred_name='Svakar',
            surname='von Svakar',
            allow_publish_info=True,
        )


class MemberFilterSingleAddressTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'address=fi'
        self.n_normal = 3
        self.n_staff = 5

        # Should be found by all
        Member.objects.create(
            # In street name on public Member
            given_names='Test',
            surname='von Test',
            street_address='Filipgatan 42',
            allow_publish_info=True,
        )
        Member.objects.create(
            # In city on public Member
            given_names='Test',
            surname='von Test',
            city='Filipstad',
            allow_publish_info=True,
        )
        Member.objects.create(
            # In country on public Member
            given_names='Test',
            surname='von Test',
            country='FI',
            allow_publish_info=True,
        )

        # Should only be found by staff
        Member.objects.create(
            # Hidden member
            given_names='Test',
            surname='von Test',
            street_address='Filipgatan 42',
            city='Filipstad',
            country='FI',
            allow_publish_info=False,
            dead=False,
        )
        Member.objects.create(
            # Dead member
            given_names='Test',
            surname='von Test',
            street_address='Filipgatan 42',
            city='Filipstad',
            country='FI',
            allow_publish_info=True,
            dead=True,
        )


class MemberFilterMultipleAddressesTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'address=filip+42'
        self.n_normal = 2
        self.n_staff = 4

        # Should be found by all
        Member.objects.create(
            # In city and street name on public Member
            given_names='Test',
            surname='von Test',
            street_address='Vägen 42',
            city='Filipstad',
            allow_publish_info=True,
        )
        Member.objects.create(
            # In city and postal code public Member
            given_names='Test',
            surname='von Test',
            city='Filipstad',
            postal_code=1423,
            allow_publish_info=True,
        )

        # Should only be found by staff
        Member.objects.create(
            # Hidden member
            given_names='Test',
            surname='von Test',
            street_address='Filipgatan 42',
            allow_publish_info=False,
            dead=False,
        )
        Member.objects.create(
            # Dead member
            given_names='Test',
            surname='von Test',
            street_address='Filipgatan 42',
            allow_publish_info=True,
            dead=True,
        )


class MemberFilterEmailTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'email=Svakar'
        self.n_normal = 1
        self.n_staff = 3

        # Should be found by all
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            email='test@svakar.fi',
            allow_publish_info=True,
        )

        # Should only be found by staff
        Member.objects.create(
            # Hidden Member
            given_names='Test',
            surname='von Test',
            email='test@svakar.fi',
            allow_publish_info=False,
            dead=False,
        )
        Member.objects.create(
            # Dead Member
            given_names='Test',
            surname='von Test',
            email='test@svakar.fi',
            allow_publish_info=True,
            dead=True,
        )


class MemberFilterDegreeProgrammeTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'degree_programme=Svakar'
        self.n_normal = 1
        self.n_staff = 2

        # Should be found by all
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            degree_programme='Svakars linje',
            allow_publish_info=True,
            dead=False,
        )

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            degree_programme='Svakars linje',
            allow_publish_info=False,
            dead=True,
        )


class MemberFilterEnrolmentYearTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'enrolment_year_min=2000&enrolment_year_max=2010'
        self.n_normal = 3
        self.n_staff = 3

        # Should be found by all
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            enrolment_year=2000,
            allow_publish_info=False,
            dead=True,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            enrolment_year=2005,
            allow_publish_info=False,
            dead=True,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            enrolment_year=2010,
            allow_publish_info=False,
            dead=True,
        )

        # Should not be found
        Member.objects.create(
            # Outside range
            given_names='Test',
            surname='von Test',
            enrolment_year=1999,
            allow_publish_info=True,
            dead=False,
        )
        Member.objects.create(
            # Outside range
            given_names='Test',
            surname='von Test',
            enrolment_year=2011,
            allow_publish_info=True,
            dead=False,
        )


class MemberFilterGraduatedTrueTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'graduated=true'
        self.n_normal = 2
        self.n_staff = 3

        # Should be found by all
        Member.objects.create(
            # Graduated
            given_names='Test',
            surname='von Test',
            graduated=True,
            allow_publish_info=True,
        )
        Member.objects.create(
            # Has graduated year (XXX: graduated can be false)
            given_names='Test',
            surname='von Test',
            graduated=False,
            graduated_year=2000,
            allow_publish_info=True,
        )

        # Should only be found by staff
        Member.objects.create(
            # Graduated, but hidden
            given_names='Test',
            surname='von Test',
            graduated=True,
            allow_publish_info=False,
        )

        # Should not be found
        Member.objects.create(
            # Not graduated
            given_names='Test',
            surname='von Test',
            graduated=False,
            allow_publish_info=True,
        )

class MemberFilterGraduatedFalseTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        # Dummy member included
        self.query = 'graduated=false'
        self.n_normal = 2
        self.n_staff = 3

        # Should be found by all
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            graduated=False,
            allow_publish_info=True,
        )

        # Should only be found by staff
        Member.objects.create(
            # Graduated and has graduated year
            given_names='Test',
            surname='von Test',
            graduated=False,
            allow_publish_info=False,
        )

        # Should not be found
        Member.objects.create(
            # Not graduated
            given_names='Test',
            surname='von Test',
            graduated=True,
            allow_publish_info=True,
        )
        Member.objects.create(
            # Has graduated year (XXX: graduated can be false)
            given_names='Test',
            surname='von Test',
            graduated=False,
            graduated_year=2000,
            allow_publish_info=True,
        )

class MemberFilterGraduatedNullTest(MemberFilterGraduatedTrueTest):
    def setUp(self):
        super().setUp()

        # graduated is the only BooleanFilter on a hidable field, so trying out the null label for it
        # Dummy member included
        self.query = 'graduated='
        self.n_normal = len(Member.objects.all())
        self.n_staff = self.n_normal

class MemberFilterGraduatedInvalidTest(MemberFilterGraduatedTrueTest):
    def setUp(self):
        super().setUp()

        # graduated is the only BooleanFilter on a hidable field, so trying out an invalid label for it
        # Dummy member included
        # XXX: This should probably return all Members, but now the filter is being recognized as "set", so all hidden Members will be filtered out for normal users
        self.query = 'graduated=unknown'
        self.n_normal = 4
        self.n_staff = 5

class MemberFilterGraduatedYearTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'graduated_year_min=2000&graduated_year_max=2010'
        self.n_normal = 3
        self.n_staff = 3

        # Should be found by all
        Member.objects.create(
            # Inside range (XXX: Graduated can be false)
            given_names='Test',
            surname='von Test',
            graduated=False,
            graduated_year=2000,
            allow_publish_info=False,
            dead=True,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            graduated=False,
            graduated_year=2005,
            allow_publish_info=False,
            dead=True,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            graduated=False,
            graduated_year=2010,
            allow_publish_info=False,
            dead=True,
        )

        # Should not be found
        Member.objects.create(
            # Outside range
            given_names='Test',
            surname='von Test',
            graduated=True,
            graduated_year=1999,
            allow_publish_info=True,
            dead=False,
        )
        Member.objects.create(
            # Outside range
            given_names='Test',
            surname='von Test',
            graduated=True,
            graduated_year=2011,
            allow_publish_info=True,
            dead=False,
        )


class MemberFilterBirthDateTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'birth_date_after=2000-1-1&birth_date_before=2010-12-31'
        self.n_normal = 6 # Filter does not work for normal users
        self.n_staff = 3

        # Should only be found by staff
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            birth_date='2000-01-01',
            allow_publish_info=True,
            dead=False,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            birth_date='2005-07-07',
            allow_publish_info=True,
            dead=False,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            birth_date='2010-12-31',
            allow_publish_info=True,
            dead=False,
        )

        # Should not be found
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            birth_date='1999-12-31',
            allow_publish_info=True,
            dead=False,
        )
        Member.objects.create(
            # Inside range
            given_names='Test',
            surname='von Test',
            birth_date='2011-01-01',
            allow_publish_info=True,
            dead=False,
        )


class MemberFilterStudentIdTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'student_id=12345'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            student_id='12345',
            allow_publish_info=True,
            dead=False,
        )

        # Should not be found
        Member.objects.create(
            # Not correct student id
            given_names='Test',
            surname='von Test',
            student_id='123456',
            allow_publish_info=True,
            dead=False,
        )


class MemberFilterDeadTrueTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'dead=true'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            allow_publish_info=True,
            dead=True,
        )

        # Should not be found
        Member.objects.create(
            # Not dead
            given_names='Test',
            surname='von Test',
            allow_publish_info=True,
            dead=False,
        )

class MemberFilterDeadFalseTest(MemberFilterDeadTrueTest):
    def setUp(self):
        super().setUp()

        self.query = self.query.replace('true', 'false')
        self.n_staff = self.n_normal - self.n_staff


class MemberFilterModulenTrueTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'subscribed_to_modulen=true'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            subscribed_to_modulen=True,
            dead=True,
        )

        # Should not be found
        Member.objects.create(
            # Not subscribed
            given_names='Test',
            surname='von Test',
            allow_publish_info=True,
            dead=False,
        )

class MemberFilterModulenFalseTest(MemberFilterModulenTrueTest):
    def setUp(self):
        super().setUp()

        self.query = self.query.replace('true', 'false')
        self.n_staff = self.n_normal - self.n_staff


class MemberFilterStudentbladetTrueTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'allow_studentbladet=true'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            allow_studentbladet=True,
            dead=True,
        )

        # Should not be found
        Member.objects.create(
            # Not subscribed
            given_names='Test',
            surname='von Test',
            allow_publish_info=True,
            dead=False,
        )

class MemberFilterStudentbladetFalseTest(MemberFilterStudentbladetTrueTest):
    def setUp(self):
        super().setUp()

        self.query = self.query.replace('true', 'false')
        self.n_staff = self.n_normal - self.n_staff


class MemberFilterPublishInfoTrueTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'allow_publish_info=true'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 2

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            allow_publish_info=True,
            dead=True,
        )

        # Should not be found
        Member.objects.create(
            # Not subscribed
            given_names='Test',
            surname='von Test',
            dead=False,
        )

class MemberFilterPublishInfoFalseTest(MemberFilterPublishInfoTrueTest):
    def setUp(self):
        super().setUp()

        self.query = self.query.replace('true', 'false')
        self.n_staff = self.n_normal - self.n_staff


class MemberFilterCommentTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'comment=svakar'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            comment='f. von Svakar',
            allow_publish_info=True,
            dead=False,
        )

        # Should not be found
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            allow_publish_info=True,
            dead=False,
        )


class MemberFilterUsernameTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'username=svakar'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            username='svakar',
            allow_publish_info=True,
            dead=False,
        )

        # Should not be found
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            username='svakar2',
            allow_publish_info=True,
            dead=False,
        )

class MemberFilterUsernameNullTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'username=-'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 2

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            username='',
        )
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            username=None,
        )

class MemberFilterUsernameAnyTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'username=*'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should not be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            username='',
        )
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            username=None,
        )


class MemberFilterBillCodeTest(BaseAPITest, TestCases):
    def setUp(self):
        super().setUp()

        self.query = 'bill_code=1234'
        self.n_normal = 3 # Filter does not work for normal users
        self.n_staff = 1

        # Should only be found by staff
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            bill_code=1234,
            allow_publish_info=True,
            dead=False,
        )

        # Should not be found
        Member.objects.create(
            given_names='Test',
            surname='von Test',
            bill_code='12345',
            allow_publish_info=True,
            dead=False,
        )
