from django.contrib.auth.models import User
from members.models import *
from registration.models import *
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import datetime

class TestMembersPagination(APITestCase):
    def uname(self, i):
        return f"svakar{i}"

    def url(self, limit, offset):
        return f'/api/members/?username=*&limit={limit}&offset={offset}'

    def test_pagination(self):
        M = 3512
        N = 1432
        User.objects.create_superuser(username='svakar', password='teknolog')
        for i in range(M):
            Member.objects.create(
                username=self.uname(i),
            )
        for i in range(N):
            Member.objects.create()

        self.client.login(username='svakar', password='teknolog')

        limit = 1000
        offset = 0
        members = []
        while True:
            response = self.client.get(self.url(limit, offset))
            j = response.json()
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(M, j['count'])
            members += j['results']
            if not j['next']:
                break
            offset += limit

        self.assertEqual(M, len(members))

        usernames = []
        ids = []
        for m in members:
            u = m['username']
            i = m['id']
            self.assertFalse(u in usernames)
            self.assertFalse(i in ids)
            usernames.append(u)
            usernames.append(i)
