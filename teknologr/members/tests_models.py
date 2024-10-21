from django.test import TestCase
from members.models import *
from ldap import LDAPError
from datetime import date, timedelta
import random

def shuffle(l):
    return random.sample(l, len(l))

class BaseTest(TestCase):
    test_names = [
        '123',
        'abc',
        'Abc',
        'åbc',
        'Åbc',
        'äbc',
        'Äbc',
        'öbc',
        'Öbc',
    ]
    test_dates = [
        date(1999, 7, 1),
        date(1999, 7, 30),
        date(2023, 6, 1),
        date(2023, 6, 13),
        date(2023, 6, 30),
        date(2030, 5, 1),
        date(2030, 5, 30),
    ]
    test_date_pairs = [
        [date(2022, 1, 1), date(2023, 1, 1)],
        [date(2023, 1, 1), date(2023, 7, 7)],
        [date(2023, 2, 2), date(2023, 11, 11)],
        [date(2023, 1, 1), date(2023, 12, 31)],
        [date(2023, 7, 7), date(2023, 12, 31)],
        [date(2022, 1, 1), date(2024, 1, 1)],
        [date(2023, 1, 1), date(2024, 1, 1)],
    ]


class MemberTest(TestCase):
    def setUp(self):
        # Normal person
        self.member1 = Member.objects.create(
            given_names='Foo Bar Baz',
            preferred_name='Foo',
            surname='Tester',
            street_address='Otsvängen 22',
            postal_code='02150',
            city='Esbo',
        )
        # Only one given name
        # No preferred name set
        # Address is not in Finland
        self.member2 = Member.objects.create(
            given_names='Foo Bar Baz',
            surname='Tester',
            street_address='Dr. Martin Luther King Boulevard #78',
            postal_code='',
            city='Williemstad',
            country='CW',
            allow_publish_info=True,
        )
        # Preferred name is not the first name
        # Surname with prefixes
        # Address is incomplete
        self.member3 = Member.objects.create(
            given_names='Foo-Bar Biz-Baz',
            preferred_name='Baz',
            surname='von der Tester',
            street_address='Otsvängen 22',
            allow_publish_info=True,
            dead=True,
        )

        MemberType.objects.create(
            begin_date=date(2020, 1, 1),
            type='OM',
            member=self.member2,
        )
        MemberType.objects.create(
            begin_date=date(2020, 1, 1),
            type='OM',
            member=self.member3,
        )

    def test_get_given_names(self):
        self.assertEqual(self.member1.get_given_names(), ['Foo', 'Bar', 'Baz'])
        self.assertEqual(self.member2.get_given_names(), ['Foo', 'Bar', 'Baz'])
        self.assertEqual(self.member3.get_given_names(), ['Foo-Bar', 'Biz-Baz'])

    def test_get_preferred_name(self):
        self.assertEqual(self.member1.get_preferred_name(), 'Foo')
        self.assertEqual(self.member2.get_preferred_name(), 'Foo')
        self.assertEqual(self.member3.get_preferred_name(), 'Baz')

    def test_get_given_names_with_initials(self):
        self.assertEqual(self.member1.get_given_names_with_initials(), 'Foo B B')
        self.assertEqual(self.member2.get_given_names_with_initials(), 'Foo B B')
        self.assertEqual(self.member3.get_given_names_with_initials(), 'F-B Biz-Baz')

    def test_get_surname_without_prefixes(self):
        self.assertEqual(self.member1.get_surname_without_prefixes(), 'Tester')
        self.assertEqual(self.member2.get_surname_without_prefixes(), 'Tester')
        self.assertEqual(self.member3.get_surname_without_prefixes(), 'Tester')

    def test_get_full_name_HTML(self):
        self.assertEqual(self.member1.get_full_name_HTML(), '<u>Foo</u> Bar Baz Tester')
        self.assertEqual(self.member2.get_full_name_HTML(), '<u>Foo</u> Bar Baz Tester')
        self.assertEqual(self.member3.get_full_name_HTML(), 'Foo-Bar Biz-<u>Baz</u> von der Tester')

    def test_full_name(self):
        self.assertEqual(self.member1.full_name, 'Foo Bar Baz Tester')
        self.assertEqual(self.member2.full_name, 'Foo Bar Baz Tester')
        self.assertEqual(self.member3.full_name, 'Foo-Bar Biz-Baz von der Tester')

    def test_full_name_for_sorting(self):
        self.assertEqual(self.member1.full_name_for_sorting, 'Tester, Foo Bar Baz')
        self.assertEqual(self.member2.full_name_for_sorting, 'Tester, Foo Bar Baz')
        self.assertEqual(self.member3.full_name_for_sorting, 'Tester, Foo-Bar Biz-Baz')

    def test_public_full_name(self):
        self.assertEqual(self.member1.public_full_name, 'Foo B B Tester')
        self.assertEqual(self.member2.public_full_name, 'Foo Bar Baz Tester')
        self.assertEqual(self.member3.public_full_name, 'F-B Biz-Baz von der Tester')

    def test_public_full_name_for_sorting(self):
        self.assertEqual(self.member1.public_full_name_for_sorting, 'Tester, Foo B B')
        self.assertEqual(self.member2.public_full_name_for_sorting, 'Tester, Foo Bar Baz')
        self.assertEqual(self.member3.public_full_name_for_sorting, 'Tester, F-B Biz-Baz')

    def test_name(self):
        self.assertFalse(hasattr(self.member1, 'name'))

    def test_empty_given_names(self):
        # This should not be possible, at least not anymore, but still need to make sure nothing breakes if it happens
        self.member1.given_names = ""
        self.member1.preferred_name = ""
        self.assertEqual(self.member1.get_given_names(), [""])
        self.assertEqual(self.member1.get_preferred_name(), "")
        self.assertEqual(self.member1.get_given_names_with_initials(), "")
        self.assertEqual(self.member1.get_full_name_HTML(), " Tester")
        self.assertEqual(self.member1.full_name, " Tester")
        self.assertEqual(self.member1.public_full_name, " Tester")

    def test_address(self):
        self.assertEquals('Otsvängen 22, 02150 Esbo, Finland', self.member1.full_address)

    def test_address_foreign(self):
        self.assertEquals('Dr. Martin Luther King Boulevard #78, Williemstad, Curaçao', self.member2.full_address)

    def test_address_incomplete(self):
        self.assertEquals('Otsvängen 22, Finland', self.member3.full_address)

    def test_str(self):
        self.assertEqual('Foo B B Tester', str(self.member1))
        self.assertEqual('Foo Bar Baz Tester', str(self.member2))
        self.assertEqual('F-B Biz-Baz von der Tester', str(self.member3))

    def test_search_by_name(self):
        Member.objects.create(given_names='Bar Foo', surname='von Test', allow_publish_info=False)
        Member.objects.create(given_names='Test', surname='Test', allow_publish_info=False, comment="foo")
        Member.objects.create(given_names='Test', surname='Test', allow_publish_info=False, username="afood")
        self.assertEqual(3, len(Member.objects.search_by_name(["foo"], False)))
        self.assertEqual(6, len(Member.objects.search_by_name(["foo"], True)))
        self.assertEqual(1, len(Member.objects.search_by_name(["foo", "von"], False)))
        self.assertEqual(2, len(Member.objects.search_by_name(["foo", "von"], True)))

    def test_member_type(self):
        member = Member(given_names='Svatta', surname='Teknolog')
        member.save()

        # test that there are no membertypes yet
        self.assertEquals('', member.current_member_type)

        # add some member types. First default member type phux
        ph = MemberType(member=member, begin_date=date(2012, 9, 1))
        ph.save()
        # A 'Phux' is not a real member type and should return ''
        self.assertEquals('', member.current_member_type)
        self.assertFalse(member.is_valid_member())

        # Make our person a 'real member'
        om = MemberType(member=member, type='OM', begin_date=date(2012, 9, 27))
        om.save()
        self.assertEquals('Ordinarie Medlem', member.current_member_type)
        self.assertTrue(member.is_valid_member())

        self.assertEquals('Ordinarie Medlem: 2012-09-27 ->', str(om))

        # Wappen kom, phuxen är inte mera phux!
        ph.end_date = date(2012, 4, 30)
        ph.save()
        self.assertEquals('Phux: 2012-09-01 – 2012-04-30', str(ph))
        self.assertFalse(member.should_be_stalm())

        # Our person became JuniorStÄlM :O
        js = MemberType(member=member, type='JS', begin_date=date(2017, 10, 15))
        js.save()
        self.assertFalse(member.should_be_stalm())

        # Our person is now finished with his/her studies
        om.end_date = date(2019, 4, 30)
        om.save()
        self.assertEquals('Ordinarie Medlem: 2012-09-27 – 2019-04-30', str(om))

        # member type should be nothing ('') now
        self.assertEquals('', member.current_member_type)
        # and person should become StÄlM now
        self.assertTrue(member.should_be_stalm())

        fg = MemberType(member=member, type='FG', begin_date=date(2019, 5, 1))
        fg.save()

        st = MemberType(member=member, type='ST', begin_date=date(2019, 5, 16))
        st.save()
        self.assertEquals('StÄlM', member.current_member_type)
        self.assertFalse(member.should_be_stalm())


class MemberOrderTest(BaseTest):
    def test_order_by(self):
        surnames = ['Aqz', 'af Xyz', 'Åäö', 'von af Ööö']

        for surname in shuffle(surnames):
            for given_names in shuffle(self.test_names):
                Member.objects.create(given_names=given_names, surname=surname)

        members = list(Member.objects.all())
        Member.order_by(members, 'name')

        self.assertEquals(len(self.test_names)*len(surnames), len(members))

        for i, surname in enumerate(surnames):
            for j, given_names in enumerate(self.test_names):
                member = members[i*len(self.test_names) + j]
                self.assertEqual(surname, member.surname)
                self.assertEqual(given_names, member.given_names)


class DecorationOwnerShipTest(TestCase):
    def setUp(self):
        member = Member.objects.create(given_names='Foo Bar', preferred_name='Foo', surname='Tester')
        decoration = Decoration.objects.create(name='Test Decoration')
        self.ownership = DecorationOwnership.objects.create(
            member=member,
            decoration=decoration,
            acquired=date.today(),
        )

    def test_str(self):
        self.assertEqual('Test Decoration - Foo B Tester', str(self.ownership))

class DecorationOwnerShipOrderTest(BaseTest):
    def setUp(self):
        for name in shuffle(self.test_names):
            member = Member.objects.create(given_names=name, surname=name)
            decoration = Decoration.objects.create(name=name)
            for d in shuffle(self.test_dates):
                DecorationOwnership.objects.create(
                    member=member,
                    decoration=decoration,
                    acquired=d,
                )

        self.ownerships = list(DecorationOwnership.objects.all())
        self.assertEquals(len(self.test_names)*len(self.test_dates), len(self.ownerships))

    def test_order_by_name(self):
        DecorationOwnership.order_by(self.ownerships, 'name')
        i = 0
        for name in self.test_names:
            for _ in self.test_dates:
                self.assertEqual(name, self.ownerships[i].decoration.name)
                i += 1

    def test_order_by_member(self):
        DecorationOwnership.order_by(self.ownerships, 'member')
        i = 0
        for name in self.test_names:
            for _ in self.test_dates:
                self.assertEqual(name, self.ownerships[i].member.surname)
                i += 1

    def test_order_by_date(self):
        DecorationOwnership.order_by(self.ownerships, 'date')
        i = 0
        for date in self.test_dates:
            for _ in self.test_names:
                self.assertEqual(date, self.ownerships[i].acquired)
                i += 1


class DecorationTest(BaseTest):
    def test_str(self):
        name = 'My decoration'
        decoration = Decoration.objects.create(name=name)
        self.assertEqual(name, str(decoration))

    def test_order_by(self):
        for name in shuffle(self.test_names):
            Decoration.objects.create(name=name)

        decorations = list(Decoration.objects.all())
        Decoration.order_by(decorations, 'name')

        self.assertEquals(len(self.test_names), len(decorations))

        for i, name in enumerate(self.test_names):
            self.assertEqual(name, decorations[i].name)


class GroupTest(TestCase):
    def setUp(self):
        group_type = GroupType.objects.create(name='Group Type')
        self.group1 = Group.objects.create(
            grouptype=group_type,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 6, 14),
        )
        self.group2 = Group.objects.create(
            grouptype=group_type,
            begin_date=date(2023, 6, 14),
            end_date=date(2023, 12, 31),
        )
        self.group3 = Group.objects.create(
            grouptype=group_type,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )
        self.group4 = Group.objects.create(
            grouptype=group_type,
            begin_date=date(2022, 1, 1),
            end_date=date(2024, 12, 31),
        )

    def test_str(self):
        self.assertEqual('Group Type: 2023-01-01 – 2023-06-14', str(self.group1))
        self.assertEqual('Group Type: 2023-06-14 – 2023-12-31', str(self.group2))
        self.assertEqual('Group Type: 2023-01-01 – 2023-12-31', str(self.group3))
        self.assertEqual('Group Type: 2022-01-01 – 2024-12-31', str(self.group4))

    def test_duration(self):
        self.assertEqual('1 januari – 14 juni 2023', str(self.group1.duration))
        self.assertEqual('14 juni – 31 december 2023', str(self.group2.duration))
        self.assertEqual('2023', str(self.group3.duration))
        self.assertEqual('2022–2024', str(self.group4.duration))

class GroupOrderTest(BaseTest):
    def setUp(self):
        for name in shuffle(self.test_names):
            group_type = GroupType.objects.create(name=name)
            for date in shuffle(self.test_dates):
                Group.objects.create(
                    grouptype=group_type,
                    begin_date=date,
                    end_date=date + timedelta(days=1),
                )

        self.groups = list(Group.objects.all())
        self.assertEquals(len(self.test_names)*len(self.test_dates), len(self.groups))

    def test_order_by_name(self):
        Group.order_by(self.groups, 'name')
        i = 0
        for name in self.test_names:
            for _ in self.test_dates:
                self.assertEqual(name, self.groups[i].grouptype.name)
                i += 1

    def test_order_by_date(self):
        Group.order_by(self.groups, 'date')
        i = 0
        for date in self.test_dates:
            for _ in self.test_names:
                self.assertEqual(date, self.groups[i].begin_date)
                i += 1

    def test_order_by_date_complex(self):
        group_type = GroupType.objects.get(pk=1)
        groups = [Group.objects.create(grouptype=group_type, begin_date=begin_date, end_date=end_date) for [begin_date, end_date] in shuffle(self.test_date_pairs)]

        self.assertEquals(len(self.test_date_pairs), len(groups))

        Functionary.order_by(groups, 'date')
        i = 0
        for [begin_date, end_date] in self.test_date_pairs:
            self.assertEqual(begin_date, groups[i].begin_date)
            self.assertEqual(end_date, groups[i].end_date)
            i += 1


class GroupTypeTest(BaseTest):
    def test_str(self):
        name = 'My group type'
        group_type = GroupType.objects.create(name=name)
        self.assertEqual(name, str(group_type))

    def test_order_by(self):
        for name in shuffle(self.test_names):
            GroupType.objects.create(name=name)

        group_types = list(GroupType.objects.all())
        GroupType.order_by(group_types, 'name')

        self.assertEquals(len(self.test_names), len(group_types))

        for i, name in enumerate(self.test_names):
            self.assertEqual(name, group_types[i].name)


class FunctionaryTest(BaseTest):
    def setUp(self):
        functionary_type = FunctionaryType.objects.create(name='Functionary Type')
        member = Member.objects.create(given_names='Foo Bar', preferred_name='Foo', surname='Tester')
        self.functionary1 = Functionary.objects.create(
            functionarytype=functionary_type,
            member=member,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 6, 14),
        )
        self.functionary2 = Functionary.objects.create(
            functionarytype=functionary_type,
            member=member,
            begin_date=date(2023, 6, 14),
            end_date=date(2023, 12, 31),
        )
        self.functionary3 = Functionary.objects.create(
            functionarytype=functionary_type,
            member=member,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )
        self.functionary4 = Functionary.objects.create(
            functionarytype=functionary_type,
            member=member,
            begin_date=date(2022, 1, 1),
            end_date=date(2024, 12, 31),
        )

    def test_str(self):
        self.assertEqual('Functionary Type: 2023-01-01 – 2023-06-14, Foo B Tester', str(self.functionary1))
        self.assertEqual('Functionary Type: 2023-06-14 – 2023-12-31, Foo B Tester', str(self.functionary2))
        self.assertEqual('Functionary Type: 2023-01-01 – 2023-12-31, Foo B Tester', str(self.functionary3))
        self.assertEqual('Functionary Type: 2022-01-01 – 2024-12-31, Foo B Tester', str(self.functionary4))

    def test_duration(self):
        self.assertEqual('1 januari – 14 juni 2023', str(self.functionary1.duration))
        self.assertEqual('14 juni – 31 december 2023', str(self.functionary2.duration))
        self.assertEqual('2023', str(self.functionary3.duration))
        self.assertEqual('2022–2024', str(self.functionary4.duration))

class FunctionaryOrderTest(BaseTest):
    def setUp(self):
        for name in shuffle(self.test_names):
            member = Member.objects.create(given_names=name, surname=name)
            functionary_type = FunctionaryType.objects.create(name=name)
            for date in shuffle(self.test_dates):
                Functionary.objects.create(
                    member=member,
                    functionarytype=functionary_type,
                    begin_date=date,
                    end_date=date + timedelta(days=1),
                )

        self.functionaries = list(Functionary.objects.all())
        self.assertEquals(len(self.test_names)*len(self.test_dates), len(self.functionaries))

    def test_order_by_name(self):
        Functionary.order_by(self.functionaries, 'name')
        i = 0
        for name in self.test_names:
            for _ in self.test_dates:
                self.assertEqual(name, self.functionaries[i].functionarytype.name)
                i += 1

    def test_order_by_member(self):
        Functionary.order_by(self.functionaries, 'member')
        i = 0
        for name in self.test_names:
            for _ in self.test_dates:
                self.assertEqual(name, self.functionaries[i].member.surname)
                i += 1

    def test_order_by_date(self):
        Functionary.order_by(self.functionaries, 'date')
        i = 0
        for date in self.test_dates:
            for _ in self.test_names:
                self.assertEqual(date, self.functionaries[i].begin_date)
                i += 1

    def test_order_by_date_complex(self):
        member = Member.objects.get(pk=1)
        functionary_type = FunctionaryType.objects.get(pk=1)
        functionaries = [Functionary.objects.create(member=member, functionarytype=functionary_type, begin_date=begin_date, end_date=end_date) for [begin_date, end_date] in shuffle(self.test_date_pairs)]

        self.assertEquals(len(self.test_date_pairs), len(functionaries))

        Functionary.order_by(functionaries, 'date')
        i = 0
        for [begin_date, end_date] in self.test_date_pairs:
            self.assertEqual(begin_date, functionaries[i].begin_date)
            self.assertEqual(end_date, functionaries[i].end_date)
            i += 1


class FunctionaryTypeTest(BaseTest):
    def test_str(self):
        name = 'My functionary type'
        functionary_type = FunctionaryType.objects.create(name=name)
        self.assertEqual(name, str(functionary_type))

    def test_order_by_name(self):
        for name in shuffle(self.test_names):
            FunctionaryType.objects.create(name=name)

        functionary_types = list(FunctionaryType.objects.all())
        FunctionaryType.order_by(functionary_types, 'name')

        self.assertEquals(len(self.test_names), len(functionary_types))

        for i, name in enumerate(self.test_names):
            self.assertEqual(name, functionary_types[i].name)


class MemberTypeTest(BaseTest):
    def setUp(self):
        member = Member.objects.create(given_names='Foo Bar', preferred_name='Foo', surname='Tester')
        self.member_type1 = MemberType.objects.create(
            type='OM',
            member=member,
            begin_date=date(2023, 1, 1),
            end_date=date(2023, 6, 14),
        )
        self.member_type2 = MemberType.objects.create(
            type='OM',
            member=member,
            begin_date=date(2023, 6, 14),
        )

    def test_str(self):
        self.assertEqual('Ordinarie Medlem: 2023-01-01 – 2023-06-14', str(self.member_type1))
        self.assertEqual('Ordinarie Medlem: 2023-06-14 ->', str(self.member_type2))


class MemberTypeOrderTest(BaseTest):
    def setUp(self):
        for name in shuffle(self.test_names):
            member = Member.objects.create(given_names=name, surname=name)
            for date in shuffle(self.test_dates):
                MemberType.objects.create(
                    member=member,
                    begin_date=date,
                    end_date=date + timedelta(days=1),
                )

        self.member_types = list(MemberType.objects.all())
        self.assertEquals(len(self.test_names)*len(self.test_dates), len(self.member_types))

    def test_order_by_member(self):
        MemberType.order_by(self.member_types, 'member')
        i = 0
        for name in self.test_names:
            for _ in self.test_dates:
                self.assertEqual(name, self.member_types[i].member.surname)
                i += 1

    def test_order_by_begin_date(self):
        MemberType.order_by(self.member_types, 'begin_date')
        i = 0
        for date in self.test_dates:
            for _ in self.test_names:
                self.assertEqual(date, self.member_types[i].begin_date)
                i += 1

    def test_order_by_end_date(self):
        MemberType.order_by(self.member_types, 'end_date')
        i = 0
        for date in self.test_dates:
            for _ in self.test_names:
                self.assertEqual(date, self.member_types[i].begin_date)
                i += 1
