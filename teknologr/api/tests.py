from django.contrib.auth.models import User, Group
from members.models import *
from registration.models import *
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

        d1 = '1999-01-01'
        d2 = '1999-12-31'

        self.d = Decoration.objects.create(name='My decoration')
        self.do = DecorationOwnership.objects.create(decoration=self.d, member=self.m1, acquired=d1)
        DecorationOwnership.objects.create(decoration=self.d, member=self.m2, acquired=d1)
        DecorationOwnership.objects.create(decoration=self.d, member=self.m3, acquired=d1)

        self.ft = FunctionaryType.objects.create(name='My functionarytype')
        self.f = Functionary.objects.create(functionarytype=self.ft, member=self.m1, begin_date=d1, end_date=d2)
        Functionary.objects.create(functionarytype=self.ft, member=self.m2, begin_date=d1, end_date=d2)
        Functionary.objects.create(functionarytype=self.ft, member=self.m3, begin_date=d1, end_date=d2)

        self.gt = GroupType.objects.create(name='My grouptype')
        self.g = Group.objects.create(grouptype=self.gt, begin_date=d1, end_date=d1)
        self.gm = GroupMembership.objects.create(group=self.g, member=self.m1)
        g2 = Group.objects.create(grouptype=self.gt, begin_date=d2, end_date=d2)
        GroupMembership.objects.create(group=g2, member=self.m1)
        GroupMembership.objects.create(group=g2, member=self.m2)
        GroupMembership.objects.create(group=g2, member=self.m3)

        self.mt = MemberType.objects.create(member=self.m1, type='PH', begin_date=d1)
        MemberType.objects.create(member=self.m2, type='PH', begin_date=d1)
        MemberType.objects.create(member=self.m3, type='PH', begin_date=d1)

        self.a = Applicant.objects.create(
            given_names='Märta',
            preferred_name='Märta',
            surname='von Teknolog',
            birth_date='1993-03-03',
        )

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

    def check_status_code(self, response, status_code):
        self.assertEqual(response.status_code, status_code, response.data if 'data' in response else None)


'''
Test implementation classes that implements all the tests. The test case classes then sets up their own test data and extends from these classes to get the sutiable tests.
'''

class CheckJSON():
    def __check_type(self, value, t):
        return (t is None and value is None) or type(value) == t

    def __check_types(self, value, t):
        if t in [dict, list]:
            raise Exception('Be more specific please')

        # Dict works as sub-objects
        if type(t) is dict:
            return self.__check_type(value, dict) and self.check_response(value, t)

        # List works as sub-arrays
        if type(t) is list:
            if len(t) != 1:
                raise Exception('Can only check the list elements against one type')

            # The required structure is a list
            if not self.__check_type(value, list):
                return False

            # Getting a list with length 0 is pretty useless, so make a better test
            if len(value) == 0:
                return False

            # Check the structure for each element
            for element in value:
                if not self.__check_types(element, t[0]):
                    return False
            return True

        # Tuple works as a union of types
        if type(t) is tuple:
            ok = False
            for tt in t:
                ok |= self.__check_type(value, tt)
            return ok

        return self.__check_type(value, t)

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
        self.check_status_code(response, status.HTTP_403_FORBIDDEN)

    def test_get_all_for_user(self):
        self.login_user()
        response = self.get_all()
        if self.columns_public is None:
            return self.check_status_code(response, status.HTTP_403_FORBIDDEN)
        self.check_status_code(response, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], self.n_all)
        self.check_response(response.json()['results'][0], self.columns_public)

    def test_get_all_for_superuser(self):
        self.login_superuser()
        response = self.get_all()
        self.check_status_code(response, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], self.n_all)
        self.check_response(response.json()['results'][0], self.columns_admin)

class GetOneMethodTests(CheckJSON):
    def test_get_one_for_anonymous_users(self):
        response = self.get_one(self.item)
        self.check_status_code(response, status.HTTP_403_FORBIDDEN)

    def test_get_one_for_user(self):
        self.login_user()
        response = self.get_one(self.item)
        columns = self.columns_public_detail if hasattr(self, 'columns_public_detail') else self.columns_public
        if columns is None:
            return self.check_status_code(response, status.HTTP_403_FORBIDDEN)
        self.check_status_code(response, status.HTTP_200_OK)
        self.check_response(response.json(), columns)

    def test_get_one_for_superuser(self):
        self.login_superuser()
        response = self.get_one(self.item)
        self.check_status_code(response, status.HTTP_200_OK)
        self.check_response(response.json(), self.columns_admin_detail if hasattr(self, 'columns_admin_detail') else self.columns_admin)

class PostMethodTests():
    def test_post_for_anonymous_users(self):
        response = self.post()
        self.check_status_code(response, status.HTTP_403_FORBIDDEN)

    def test_post_for_user(self):
        self.login_user()
        response = self.post()
        self.check_status_code(response, status.HTTP_403_FORBIDDEN)

    def test_post_for_superuser(self):
        self.login_superuser()
        response = self.post()
        self.check_status_code(response, status.HTTP_201_CREATED)


'''
Test case classes that extends one or many test implementation classes. Each test case class sets up their own custom test data.
'''

# MEMBERS

# Always shown
MEMBER_PUBLIC = {
    'id': int,
    'given_names': str,
    'preferred_name': str,
    'surname': str,
    'n_functionaries': int,
    'n_groups': int,
    'n_decorations': int,
    'degree_programme': str,
    'enrolment_year': int,
    'graduated': bool,
    'graduated_year': int,
}
# Shown if member is not hidden
MEMBER_PERSONAL = {
    **MEMBER_PUBLIC,
    'street_address': str,
    'postal_code': str,
    'city': str,
    'country': str,
    'phone': str,
    'email': str,
}
# Shown only to admins
MEMBER_ADMIN = {
    **MEMBER_PERSONAL,
    'created': str,
    'modified': str,
    'birth_date': str,
    'student_id': str,
    'dead': bool,
    'subscribed_to_modulen': bool,
    'allow_publish_info': bool,
    'allow_studentbladet': bool,
    'comment': str,
    'username': (str, None),
    'bill_code': (str, None),
}
MEMBER_DETAIL = {
    'functionaries': [{
        'functionarytype': {
            'id': int,
            'name': str,
        },
        'begin_date': str,
        'end_date': str,
    }],
    'groups': [{
        'grouptype': {
            'id': int,
            'name': str,
        },
        'begin_date': str,
        'end_date': str,
    }],
    'decorations': [{
        'decoration': {
            'id': int,
            'name': str,
        },
        'acquired': str,
    }],
}
MEMBER_PUBLIC_DETAIL = {
    **MEMBER_PUBLIC,
    **MEMBER_DETAIL,
}
MEMBER_PERSONAL_DETAIL = {
    **MEMBER_PERSONAL,
    **MEMBER_DETAIL,
}
MEMBER_ADMIN_DETAIL = {
    **MEMBER_ADMIN,
    **MEMBER_DETAIL,
    'membertypes': [{
        'type': str,
        'begin_date': str,
        'end_date': (str, None),
    }],
}

class MembersAPITest(BaseAPITest, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.columns_public = MEMBER_PUBLIC
        self.columns_admin = MEMBER_ADMIN
        self.n_all = len(self.ms)
        self.post_data = {}

    def test_get_all_structure_for_user(self):
        self.login_user()
        data = self.get_all().json()
        self.assertEqual(3, data['count'])
        results = data['results']
        self.check_response(results[0], MEMBER_PUBLIC)
        self.check_response(results[1], MEMBER_PUBLIC)
        self.check_response(results[2], MEMBER_PERSONAL)

class MemberHiddenAPITest(BaseAPITest, GetOneMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.item = self.m1
        self.columns_public_detail = MEMBER_PUBLIC_DETAIL
        self.columns_admin_detail = MEMBER_ADMIN_DETAIL

    def test_member_given_names_for_user(self):
        self.login_user()
        data = self.get_one(self.item).json()
        self.assertEqual(data.get('given_names'), 'S Svakar')

class MemberDeadAPITest(BaseAPITest, GetOneMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.item = self.m2
        self.columns_public_detail = MEMBER_PUBLIC_DETAIL
        self.columns_admin_detail = MEMBER_ADMIN_DETAIL

    def test_member_given_names_for_user(self):
        self.login_user()
        data = self.get_one(self.item).json()
        self.assertEqual(data.get('given_names'), 'S Svatta')

class MemberNormalAPITest(BaseAPITest, GetOneMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/members/'
        self.item = self.m3
        self.columns_public_detail = MEMBER_PERSONAL_DETAIL
        self.columns_admin_detail = MEMBER_ADMIN_DETAIL

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
        self.check_status_code(response, status.HTTP_403_FORBIDDEN)

    def test_search_for_user(self):
        self.login_user()
        response = self.search()
        self.check_status_code(response, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

    def test_search_for_superuser(self):
        self.login_superuser()
        response = self.search()
        self.check_status_code(response, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 4)


# DECORATIONS

class DecorationsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/decorations/'
        self.item = self.d
        self.columns_public = {'id': int, 'name': str, 'comment': str, 'n_ownerships': int}
        self.columns_public_detail = {
            **self.columns_public,
            'ownerships': [{
                'id': int,
                'acquired': str,
                'member': {'id': int, 'name': str},
            }],
        }
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.columns_admin_detail = {**self.columns_public_detail, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {'name': 'test'}

class DecorationOwnershipsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/decorationownerships/'
        self.item = self.do
        self.columns_public = {
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
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.n_all = 3
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
        self.columns_public = {
            'id': int,
            'name': str,
            'comment': str,
            'n_functionaries_total': int,
            'n_functionaries_unique': int,
        }
        self.columns_public_detail = {
            **self.columns_public,
            'functionaries': [{
                'id': int,
                'begin_date': str,
                'end_date': str,
                'member': {'id': int, 'name': str},
            }],
        }
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.columns_admin_detail = {**self.columns_public_detail, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {'name': 'test'}

class FunctionariesAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/functionaries/'
        self.item = self.f
        self.columns_public = {
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
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.n_all = 3
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
        self.columns_public = {
            'id': int,
            'name': str,
            'comment': str,
            'n_groups': int,
            'n_members_total': int,
            'n_members_unique': int,
        }
        self.columns_public_detail = {
            **self.columns_public,
            'groups': [{
                'id': int,
                'begin_date': str,
                'end_date': str,
                'n_members': int,
            }]
        }
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.columns_admin_detail = {**self.columns_public_detail, 'created': str, 'modified': str}
        self.n_all = 1
        self.post_data = {'name': 'test'}

class GroupsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/groups/'
        self.item = self.g
        self.columns_public = {
            'id': int,
            'grouptype': {
                'id': int,
                'name': str,
            },
            'begin_date': str,
            'end_date': str,
            'n_members': int,
        }
        self.columns_public_detail = {
            **self.columns_public,
            'members': [{
                'id': int,
                'name': str,
            }],
        }
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.columns_admin_detail = {**self.columns_public_detail, 'created': str, 'modified': str}
        self.n_all = 2
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
        self.columns_public = {
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
        self.columns_admin = {**self.columns_public, 'created': str, 'modified': str}
        self.n_all = 4
        self.post_data = {
            'group': self.g.id,
            'member': self.m2.id,
        }


# MEMBERTYPES

class MemberTypesAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/membertypes/'
        self.item = self.mt
        self.columns_public = None
        self.columns_admin = {
            'id': int,
            'begin_date': str,
            'end_date': (str, None),
            'type': str,
            'member': {
                'id': int,
                'name': str,
            },
            'created': str,
            'modified': str,
        }
        self.n_all = 3
        self.post_data = {
            'member': self.m2.id,
            'type': 'OM',
            'begin_date': date.today().isoformat(),
        }


# APPLICANTS

class ApplicantsAPITest(BaseAPITest, GetOneMethodTests, GetAllMethodTests, PostMethodTests):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/applicants/'
        self.item = self.mt
        self.columns_public = None
        self.columns_admin = {
            'id': int,
            'surname': str,
            'given_names': str,
            'preferred_name': str,
            'street_address': str,
            'postal_code': str,
            'city': str,
            'country': str,
            'phone': str,
            'email': str,
            'birth_date': str,
            'student_id': str,
            'degree_programme': str,
            'enrolment_year': int,
            'username': (str, None),
            'motivation': str,
            'subscribed_to_modulen': bool,
            'allow_publish_info': bool,
            'allow_studentbladet': bool,
            'mother_tongue': str,
            'created_at': str,
        }
        self.n_all = 1
        self.post_data = {
            'surname': 'Test',
            'given_names': 'Test',
            'street_address': 'Test',
            'postal_code': 'Test',
            'city': 'Test',
            'phone': 'Test',
            'email': 'test@test.com',
            'birth_date': '1999-01-01',
            'student_id': "123456",
            'degree_programme': 'Test',
        }

class RootAPIPageTests(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.api_path = '/api/'

    def test_get_for_anonymous_users(self):
        response = self.get_all()
        self.check_status_code(response, status.HTTP_403_FORBIDDEN)

    def test_get_for_user(self):
        self.login_user()
        response = self.get_all()
        self.check_status_code(response, status.HTTP_200_OK)
        self.assertEqual(8, len(response.json()))

    def test_get_for_superuser(self):
        self.login_superuser()
        response = self.get_all()
        self.check_status_code(response, status.HTTP_200_OK)
        self.assertEqual(16, len(response.json()))
