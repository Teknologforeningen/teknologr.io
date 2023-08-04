from django.contrib.auth.models import User, Group
from members.models import *
from rest_framework import status
from rest_framework.test import APITestCase

class BaseAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='svakar', password='teknolog')
        self.superuser = User.objects.create_superuser(username='superuser', password='teknolog')

        self.m1 = Member.objects.create(
            country='FI',
            given_names='Sverker Svakar',
            preferred_name='Svakar',
            surname='von Teknolog',
            street_address='OK01',
            postal_code='11111',
            city='Stad1',
            phone='040-1',
            email='1@teknolog.com',
            birth_date='1999-01-01',
            student_id='111111',
            degree_programme='Energi- och miljöteknik',
            enrolment_year=2019,
            graduated=True,
            graduated_year=2022,
            dead=False,
            subscribed_to_modulen=True,
            allow_publish_info=False,
            allow_studentbladet=True,
            comment='Kommentar',
        )
        self.m2 = Member.objects.create(
            country='FI',
            given_names='Sigrid Svatta',
            preferred_name='Svatta',
            surname='von Teknolog',
            street_address='OK02',
            postal_code='22222',
            city='Stad2',
            phone='040-2',
            email='2@teknolog.com',
            birth_date='2999-02-02',
            student_id='222222',
            degree_programme='Energi- och miljöteknik',
            enrolment_year=2019,
            graduated=True,
            graduated_year=2022,
            dead=True,
            subscribed_to_modulen=True,
            allow_publish_info=True,
            allow_studentbladet=True,
            comment='Kommentar',
        )
        self.m3 = Member.objects.create(
            country='FI',
            given_names='Test Holger Björn-Anders',
            preferred_name='Test',
            surname='von Teknolog',
            street_address='OK03',
            postal_code='33333',
            city='Stad3',
            phone='040-3',
            email='3@teknolog.com',
            birth_date='3999-03-03',
            student_id='333333',
            degree_programme='Energi- och miljöteknik',
            enrolment_year=2019,
            graduated=True,
            graduated_year=2022,
            dead=False,
            subscribed_to_modulen=True,
            allow_publish_info=True,
            allow_studentbladet=True,
            comment='Kommentar',
        )

        self.d = Decoration.objects.create(name="My decoration")
        self.do = DecorationOwnership.objects.create(decoration=self.d, member=self.m1, acquired=date.today())

        self.ft = FunctionaryType.objects.create(name="My functionarytype")
        self.f = Functionary.objects.create(functionarytype=self.ft, member=self.m1, begin_date=date.today(), end_date=date.today())

        self.gt = GroupType.objects.create(name="My grouptype")
        self.g = Group.objects.create(grouptype=self.gt, begin_date=date.today(), end_date=date.today())
        self.gm = GroupMembership.objects.create(group=self.g, member=self.m1)

        self.ms = [self.m1, self.m2, self.m3]

    def login_user(self):
        self.client.login(username='svakar', password='teknolog')

    def login_superuser(self):
        self.client.login(username='superuser', password='teknolog')

    def get_all(self):
        return self.client.get(self.api_path)

    def get_one(self, obj):
        return self.client.get(f'{self.api_path}{obj.id}/')

    def post(self):
        return self.client.post(self.api_path, self.post_data)


'''
Test implementation classes that implements all the tests. The test case classes then sets up their own test data and extends from these classes to get the sutiable tests.
'''

class CheckJSON():
    def __check_type(self, value, t):
        return (t is None and value is None) or type(value) == t

    def __check_types(self, value, types):
        if types == dict:
            raise Exception('Be more specific please')

        if type(types) is dict:
            return self.check_response(value, types)

        if type(types) is list:
            ok = False
            for t in types:
                ok |= self.__check_type(value, t)
            return ok

        return self.__check_type(value, types)

    def check_response(self, data, structure):
        ''' Check that the data from a JSON response has a specific structure '''
        self.assertEqual(len(data), len(structure), f'Length not {len(structure)}: {data}')
        for key, types in structure.items():
            self.assertTrue(key in data, f"Key '{key}' not in {data}")
            value = data[key]
            ok = self.__check_types(value, types)
            self.assertTrue(ok, f"Value of key '{key}' is '{value}', which is not of type {types}")
        return True

class GetAllMethodTests(CheckJSON):
    def test_get_all_for_anonymous_users(self):
        response = self.get_all()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_for_user(self):
        self.login_user()
        response = self.get_all()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), self.n_all)

    def test_get_all_for_superuser(self):
        self.login_superuser()
        response = self.get_all()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), self.n_all)

class GetOneMethodTests(CheckJSON):
    def test_get_one_for_anonymous_users(self):
        response = self.get_one(self.item)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_one_for_user(self):
        self.login_user()
        response = self.get_one(self.item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_response(response.json(), self.columns_partial)

    def test_get_one_for_superuser(self):
        self.login_superuser()
        response = self.get_one(self.item)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_response(response.json(), self.columns_full)

class PostMethodTests():
    def test_post_for_anonymous_users(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_for_user(self):
        self.login_user()
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_for_superuser(self):
        self.login_superuser()
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


'''
Test case classes that extends one or many test implementation classes. Each test case class sets up their own custom test data.
'''

# MEMBERS

all_member_columns = {
    'id': int,
    'country': str,
    'created': str,
    'modified': str,
    'given_names': str,
    'preferred_name': str,
    'surname': str,
    'street_address': str,
    'postal_code': str,
    'city': str,
    'phone': str,
    'email': str,
    'birth_date': str,
    'student_id': str,
    'degree_programme': str,
    'enrolment_year': int,
    'graduated': bool,
    'graduated_year': int,
    'dead': bool,
    'subscribed_to_modulen': bool,
    'allow_publish_info': bool,
    'allow_studentbladet': bool,
    'comment': str,
    'username': [str, None],
    'bill_code': [str, None],
}

class MembersAPITest(BaseAPITest, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.n_all = len(self.ms)
        self.post_data = {}

class MemberHiddenAPITest(BaseAPITest, GetOneMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.item = self.m1
        self.columns_partial = {
            'id': int,
            'given_names': str,
            'preferred_name': str,
            'surname': str,
            'degree_programme': str,
            'enrolment_year': int,
            'graduated': bool,
            'graduated_year': int,
        }
        self.columns_full = all_member_columns

    def test_member_given_names_for_user(self):
        self.login_user()
        data = self.get_one(self.item).json()
        self.assertEqual(data.get('given_names'), 'S Svakar')

class MemberDeadAPITest(BaseAPITest, GetOneMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.item = self.m2
        self.columns_partial = {
            'id': int,
            'given_names': str,
            'preferred_name': str,
            'surname': str,
            'degree_programme': str,
            'enrolment_year': int,
            'graduated': bool,
            'graduated_year': int,
        }
        self.columns_full = all_member_columns

    def test_member_given_names_for_user(self):
        self.login_user()
        data = self.get_one(self.item).json()
        self.assertEqual(data.get('given_names'), 'S Svatta')

class MemberNormalAPITest(BaseAPITest, GetOneMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.item = self.m3
        self.columns_partial = {
            'id': int,
            'given_names': str,
            'preferred_name': str,
            'surname': str,
            'street_address': str,
            'postal_code': str,
            'city': str,
            'country': str,
            'phone': str,
            'email': str,
            'degree_programme': str,
            'enrolment_year': int,
            'graduated': bool,
            'graduated_year': int,
        }
        self.columns_full = all_member_columns

    def test_member_given_names_for_user(self):
        self.login_user()
        data = self.get_one(self.item).json()
        self.assertEqual(data.get('given_names'), 'Test Holger Björn-Anders')

class MemberSearchTest(BaseAPITest):
    def setUp(self):
        super().setUp()

        # These Members should only be found by staff
        Member.objects.create(
            given_names='Sverker Svakar',
            surname='von Teknolog',
        )
        Member.objects.create(
            given_names='Test',
            surname='von Teknolog',
            email='test@svakar.fi',
        )
        Member.objects.create(
            given_names='Test',
            surname='von Teknolog',
            comment='Svakar',
        )

    def search(self):
        return self.client.get('/api/members/?search=Svakar')

    def test_search_for_anonymous_users(self):
        response = self.search()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_for_user(self):
        self.login_user()
        response = self.search()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_search_for_superuser(self):
        self.login_superuser()
        response = self.search()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)


# DECORATIONS

class DecorationsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/decorations/'
        self.item = self.d
        self.columns_partial = {'id': int, 'name': str, 'comment': str}
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {'name': 'test'}

class DecorationMembershipsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/decorationownerships/'
        self.item = self.do
        self.columns_partial = {
            'id': int,
            'decoration': {
                'id': int,
                'name': str,
            },
            'member': {
                'id': int,
                'name': str,
            },
            'acquired': str,
        }
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {
            'decoration': self.d.id,
            'member': self.m2.id,
            'acquired': date.today().isoformat(),
        }


# FUNCTIONARIES

class FunctionaryTypesAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/functionarytypes/'
        self.item = self.ft
        self.columns_partial = {'id': int, 'name': str, 'comment': str}
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {'name': 'test'}

class FunctionariesAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/functionaries/'
        self.item = self.f
        self.columns_partial = {
            'id': int,
            'functionarytype': {
                'id': int,
                'name': str,
            },
            'member': {
                'id': int,
                'name': str,
            },
            'begin_date': str,
            'end_date': str,
        }
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {
            'functionarytype': self.ft.id,
            'member': self.m2.id,
            'begin_date': date.today().isoformat(),
            'end_date': date.today().isoformat(),
        }


# GROUPS

class GroupTypesAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/grouptypes/'
        self.item = self.gt
        self.columns_partial = {'id': int, 'name': str, 'comment': str}
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {'name': 'test'}

class GroupsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/groups/'
        self.item = self.g
        self.columns_partial = {
            'id': int,
            'grouptype': {
                'id': int,
                'name': str,
            },
            'begin_date': str,
            'end_date': str,
        }
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {
            'grouptype': self.gt.id,
            'begin_date': date.today().isoformat(),
            'end_date': date.today().isoformat(),
        }

class GroupMembershipsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/groupmemberships/'
        self.item = self.gm
        self.columns_partial = {
            'id': int,
            'group': {
                'id': int,
                'grouptype': {
                    'id': int,
                    'name': str,
                },
                'begin_date': str,
                'end_date': str,
            },
            'member': {
                'id': int,
                'name': str,
            },
        }
        self.columns_full = {**self.columns_partial, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {
            'group': self.g.id,
            'member': self.m2.id,
        }
