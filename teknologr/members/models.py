# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import Q, Prefetch, Count
from django_countries.fields import CountryField
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from locale import strxfrm
from operator import attrgetter
from datetime import date
from katalogen.utils import *
from members.utils import *


class SuperClass(models.Model):
    # This class is the base of everything
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MemberManager(models.Manager):
    def all_with_related(self):
        '''
        This is done in 5 queries:
        1. SELECT Member WHERE id=member_id
        2. SELECT DecorationOwnership WHERE member__id=member_id
        3. SELECT Functionary WHERE member__id=member_id
        4. SELECT GroupMembership WHERE member__id=member_id
        5. SELECT MemberType WHERE member__id=member_id
        '''
        return Member.objects.prefetch_related(
            Prefetch('decoration_ownerships', queryset=DecorationOwnership.objects.select_related('decoration')),
            Prefetch('functionaries', queryset=Functionary.objects.select_related('functionarytype')),
            Prefetch('group_memberships', queryset=GroupMembership.objects.select_related('group', 'group__grouptype')),
            'member_types',
        ).annotate(
            count_decoration_ownerships=Count('decoration_ownerships'),
            count_functionaries=Count('functionaries'),
            count_group_memberships=Count('group_memberships'),
        )

    def get_prefetched_or_404(self, member_id):
        return get_object_or_404(self.all_with_related(), id=member_id)

    def search_by_name(self, queries, staff_search=False):
        if not queries:
            return []

        queries = [q.lower() for q in queries]
        if staff_search:
            # Search within comments too since that can include old names or nicknames
            filters = [(
                Q(given_names__icontains=q) |
                Q(preferred_name__icontains=q) |
                Q(surname__icontains=q) |
                Q(comment__icontains=q) |
                Q(email__icontains=q) |
                Q(username__icontains=q)
            ) for q in queries]
        else:
            filters = [(
                Q(given_names__icontains=q) |
                Q(preferred_name__icontains=q) |
                Q(surname__icontains=q)
            ) for q in queries]
        members = self.filter(*filters)
        members = list(members)

        # Need to remove hidden Members that were matched on a non-preferred given name
        if not staff_search:
            members = [m for m in members if m.allow_publish_info or all([q in m.surname.lower() or q in m.get_preferred_name().lower() for q in queries])]

        return members


class Member(SuperClass):
    objects = MemberManager()
    STAFF_ONLY_FIELDS = ['birth_date', 'student_id', 'dead', 'subscribed_to_modulen', 'allow_publish_info', 'allow_studentbladet', 'comment', 'username', 'bill_code']
    HIDABLE_FIELDS = ['street_address', 'postal_code', 'city', 'country', 'phone', 'email', 'degree_programme', 'enrolment_year', 'graduated', 'graduated_year']
    # NOTE: given_names is semi-hidable

    # NAMES
    given_names = models.CharField(max_length=64, blank=False, null=False, default="UNKNOWN")
    preferred_name = models.CharField(max_length=32, blank=True, null=False, default="")
    surname = models.CharField(max_length=32, blank=False, null=False, default="UNKNOWN")
    # ADDRESS
    street_address = models.CharField(max_length=64, blank=True, null=False, default="")
    postal_code = models.CharField(max_length=64, blank=True, null=False, default="")
    city = models.CharField(max_length=64, blank=True, null=False, default="")
    # https://pypi.python.org/pypi/django-countries/1.0.1
    country = CountryField(blank_label="Välj land", blank=True, null=False, default="")
    # CONTACT INFO
    phone = models.CharField(max_length=128, blank=True, null=False, default="")
    email = models.CharField(max_length=64, blank=True, null=False, default="")
    # DATE OF BIRTH
    birth_date = models.DateField(blank=True, null=True)
    # STUDIES
    student_id = models.CharField(max_length=10, blank=True, null=True, default=None, unique=True)
    degree_programme = models.CharField(max_length=256, blank=True, null=False)
    enrolment_year = models.IntegerField(blank=True, null=True)
    graduated = models.BooleanField(default=False)
    graduated_year = models.IntegerField(blank=True, null=True)
    # OTHER
    dead = models.BooleanField(default=False)
    # TODO: separate consent to own table
    subscribed_to_modulen = models.BooleanField(default=False)
    allow_publish_info = models.BooleanField(default=False)
    allow_studentbladet = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)
    # IT-username and BILL
    username = models.CharField(max_length=32, blank=False, null=True, editable=False, unique=True)
    bill_code = models.CharField(max_length=8, blank=False, null=True, editable=False)

    def __init__(self, *args, **kwargs):
        super(Member, self).__init__(*args, **kwargs)
        # Store original email so we can check if it has changed on save
        self._original_email = self.email

    def __str__(self):
        return self.public_full_name

    '''
    Names are complicated...
    - Given names (or first names)
        * Mandatory
        * Can be one or many
    - Preferred name
        * Not mandatory
        * If present, must be one of the given names (but that restriction is not currently implemented)
        * If empty, it is assumed that the first given name is the preferred name
    - Surname
        * Mandatory
        * Can be one or many
        * Can include prefixes such as 'von' or 'af' that need to be taken into consideration when sorting is applied. For example, 'von Numers' should be sorted by 'N', not 'V'.

    Members can choose to not have their information public, meaning that at least contact information such as email, phone number and addresses should be hidden to normal users, but does this also apply to for example middle names? We use middle names for uniquely identifying people with the same first and last names, and the amount of duplicate names is not negligible. I don't think anyone actually has a problem revealing their middle names, but I'm not 100% sure about that... The compromise would be to write the non-preferred given names as initials, such as 'Kalle C J Anka' or 'K-G Kalle M Anka'.

    So there need to be at least 5 different name methods/properties:
    - common_name
        = '<preferred_name> <surname>'
    - full_name or name
        = '<given_names> <surname>'
    - public_full_name
        = '<preferred_name> <remaining given_names initials> <surname>'
    - full_name_for_sorting
        = '<surname with removed prefix> <given_names>'
    - public_full_name_for_sorting
        = '<surname with removed prefix> <preferred_name> <remaining given_names initials>'
    '''

    def get_given_names(self):
        # Make sure to return a list with at least one element
        return self.given_names.split() if self.given_names else ['']

    def get_preferred_name(self):
        return self.preferred_name or self.get_given_names()[0]

    def get_given_names_with_initials(self):
        '''
        All given names except the preferred one is converted to initials:
         - _Foo_ Bar Baz -> Foo B B
         - _Foo-Bar_ Baz -> Foo-Bar B
         - Foo-_Bar_ Baz -> Foo-Bar B # XXX: Or is 'F-Bar B' better?
         - _Foo_-Bar Baz -> Foo-Bar B # XXX: Or is 'Foo-B B' better?
         - Foo Bar _Baz_ -> F B Baz
         - Foo-Bar _Baz_ -> F-B Baz
        '''
        preferred_name = self.get_preferred_name()
        names = [n if preferred_name in n else '-'.join([nn[0] for nn in n.split('-')]) for n in self.get_given_names()]
        return " ".join(names)

    def get_surname_without_prefixes(self):
        # Surname prefixes such as 'von' or 'af' should always be written out, but is usually not considered when sorting names alphabethically. There are even surnames with more than one prefix. For example, 'von der Leyen' should be sorted by 'L'.

        # Let's assume the prefixes in question are always written with lowercase, and that everything written in all lowercase are prefixes...
        surname = self.surname
        return surname.lstrip('abcdefghijklmnopqrstuvwxyzåäö ') or surname.split()[-1]

    def get_full_name_HTML(self):
        '''
        Return name with the preferred name undercored. This can go wrong if the preferred name is not set correctly to one of the given names.

        NOTE: A.replace(B, C) can be a bit confusing in Python if B = "" is used, since the empty string "" is assumed to be "everywhere" in Python strings:
            "abc".replace("", "X")    => "XaXbXcX"
               "".replace("", "X")    => "X"
        In addition, pre Python 3.9 the extended method A.replace(B, C, N) was bugged if B = "" was used:
            "abc".replace("", "X", 1) => "Xabc" (OK)
               "".replace("", "X", 1) => ""     (INCONSISTENT)
        So replacing empty strings can be tricky, especially if the autobuilds run a different Python version than you.
        '''
        preferred_name = self.get_preferred_name()
        given_names_HTML = self.given_names.replace(preferred_name, f"<u>{preferred_name}</u>", 1) if preferred_name else self.given_names
        return format_html(f'{given_names_HTML} {self.surname}')

    @property
    def common_name(self):
        return f'{self.get_preferred_name()} {self.surname}'

    @property
    def full_name(self):
        return f'{self.given_names} {self.surname}'

    @property
    def public_full_name(self):
        if self.showContactInformation():
            return self.full_name
        return f'{self.get_given_names_with_initials()} {self.surname}'

    @property
    def full_name_for_sorting(self):
        return f'{self.get_surname_without_prefixes()}, {self.given_names}'

    @property
    def public_full_name_for_sorting(self):
        if self.showContactInformation():
            return self.full_name_for_sorting
        return f'{self.get_surname_without_prefixes()}, {self.get_given_names_with_initials()}'

    @property
    def current_member_type(self):
        member_type = self.getMostRecentMemberType()

        if member_type:
            return member_type.get_type_display()
        else:
            return ""

    @property
    def full_address(self):
        country = 'Finland'
        if self.country.name:
            country = str(self.country.name)
        city = f'{self.postal_code} {self.city}'.strip()
        address_parts = [self.street_address, city, country]
        return ", ".join([s for s in address_parts if s])

    @property
    def subscribed_to_modulen_text(self):
        return "Ja" if self.subscribed_to_modulen else "Nej"

    @property
    def allow_studentbladet_text(self):
        return "Ja" if self.allow_studentbladet else "Nej"

    @property
    def allow_publish_info_text(self):
        return "Ja" if self.allow_publish_info else "Nej"

    @property
    def n_decorations(self):
        if hasattr(self, 'count_decoration_ownerships'):
            return self.count_decoration_ownerships
        return self.decoration_ownerships.count()

    @property
    def n_functionaries(self):
        if hasattr(self, 'count_functionaries'):
            return self.count_functionaries
        return self.functionaries.count()

    @property
    def n_groups(self):
        if hasattr(self, 'count_group_memberships'):
            return self.count_group_memberships
        return self.group_memberships.count()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = None
        if not self.student_id:
            self.student_id = None

        # Sync email to LDAP if changed
        error = None
        if self.username and self.email != self._original_email:
            from api.ldap import LDAPAccountManager
            from ldap import LDAPError
            try:
                with LDAPAccountManager() as lm:
                    # Skip syncing email to LDAP if the LDAP account does not exist
                    if lm.check_account(self.username):
                        lm.change_email(self.username, self.email)
            except LDAPError as e:
                # Could not update LDAP, save other fields but keep original email
                self.email = self._original_email
                # Raise an error anyway to notify user
                error = e

        super(Member, self).save(*args, **kwargs)
        if error:
            raise error

    def getMostRecentMemberType(self):
        types = self.member_types.all()

        if (len(types)) == 0:
            return None

        ordinarie = next((x for x in types if x.type == "OM"), None)
        if ordinarie and not ordinarie.end_date:
            return ordinarie

        stalm = next((x for x in types if x.type == "ST"), None)
        if stalm and not stalm.end_date:
            return stalm

        return None

    def shouldBeStalm(self):
        ''' Used to find Juniorstalmar members that should magically become stalmar somehow '''
        return not self.isValidMember() and ("JS" in [x.type for x in MemberType.objects.filter(member=self)])

    def isValidMember(self):
        memberType = self.getMostRecentMemberType()
        return memberType is not None and (memberType.type == "OM" or memberType.type == "ST")

    @property
    def phux_year(self):
        types = self.member_types.all()
        # XXX: Do we need to take into account multiple Phux MemberTypes?
        member_type_phux = next((x for x in types if x.type == "PH"), None)
        return member_type_phux.begin_date.year if member_type_phux else None

    def showContactInformation(self):
        return self.allow_publish_info and not self.dead

    @classmethod
    def get_show_info_Q(cls):
        return Q(allow_publish_info=True, dead=False)

    @property
    def decoration_ownerships_by_date(self):
        l = list(self.decoration_ownerships.all())
        DecorationOwnership.order_by(l, 'name')
        DecorationOwnership.order_by(l, 'date', True)
        return l

    @property
    def functionaries_by_date(self):
        l = list(self.functionaries.all())
        Functionary.order_by(l, 'name')
        Functionary.order_by(l, 'date', True)
        return l

    @property
    def group_memberships_by_date(self):
        l = list(self.group_memberships.all())
        GroupMembership.order_by(l, 'name')
        GroupMembership.order_by(l, 'date', True)
        return l

    @classmethod
    def order_by(cls, members_list, by, reverse=False):
        if by == 'name':
            key = lambda m: strxfrm(m.full_name_for_sorting)
        else:
            return
        members_list.sort(key=key, reverse=reverse)


class DecorationOwnershipManager(models.Manager):
    def all_with_related(self):
        return self.get_queryset().select_related('decoration', 'member')

    def year(self, year):
        return self.all_with_related().filter(acquired__year=year)

    def year_ordered(self, year):
        l = list(self.year(year))
        DecorationOwnership.order_by(l, 'member')
        DecorationOwnership.order_by(l, 'name')
        return l

class DecorationOwnership(SuperClass):
    objects = DecorationOwnershipManager()
    member = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="decoration_ownerships")
    decoration = models.ForeignKey("Decoration", on_delete=models.CASCADE, related_name="ownerships")
    acquired = models.DateField()

    def __str__(self):
        return f'{self.decoration.name} - {self.member}'

    @classmethod
    def order_by(cls, ownerships_list, by, reverse=False):
        if by == 'date':
            key = attrgetter('acquired')
        elif by == 'name':
            key = lambda do: strxfrm(do.decoration.name)
        elif by == 'member':
            key = lambda do: strxfrm(do.member.full_name_for_sorting)
        else:
            return
        ownerships_list.sort(key=key, reverse=reverse)

class DecorationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(count=Count('ownerships'))

    def all_by_name(self):
        l = list(self.get_queryset())
        Decoration.order_by(l, 'name')
        return l

    def get_prefetched_or_404(self, decoration_id):
        '''
        This is done in 2 queries:
        1. SELECT Decoration WHERE id=decoration_id
        2. SELECT DecorationOwnership WHERE decoration__id=decoration_id
        '''
        queryset = Decoration.objects.prefetch_related(
            Prefetch('ownerships', queryset=DecorationOwnership.objects.select_related('member')),
        )
        return get_object_or_404(queryset, id=decoration_id)

class Decoration(SuperClass):
    objects = DecorationManager()
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)
    comment = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    @property
    def n_ownerships(self):
        if hasattr(self, 'count'):
            return self.count
        return self.ownerships.count()

    @property
    def ownerships_by_date(self):
        l = list(self.ownerships.all())
        DecorationOwnership.order_by(l, 'member')
        DecorationOwnership.order_by(l, 'date', True)
        return l

    @classmethod
    def order_by(cls, decorations_list, by, reverse=False):
        if by == 'name':
            key = lambda d: strxfrm(d.name)
        else:
            return
        decorations_list.sort(key=key, reverse=reverse)


class GroupMembership(SuperClass):
    class GMManager(models.Manager):
        def all_with_related(self):
            return self.get_queryset().select_related('group', 'group__grouptype', 'member')

    objects = GMManager()
    member = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="group_memberships")
    group = models.ForeignKey("Group", on_delete=models.CASCADE, related_name="memberships")

    class Meta:
        unique_together = (("member", "group"),)

    @classmethod
    def order_by(cls, memberships_list, by, reverse=False):
        if by == 'date':
            key = attrgetter('group.end_date', 'group.begin_date')
        elif by == 'name':
            key = lambda gm: strxfrm(gm.group.grouptype.name)
        elif by == 'member':
            key = lambda gm: strxfrm(gm.member.full_name_for_sorting)
        else:
            return
        memberships_list.sort(key=key, reverse=reverse)


class GroupManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(num_members=Count('memberships', distinct=True))

    def year(self, year):
        return self.get_queryset().prefetch_related(
            Prefetch(
                'memberships',
                queryset=GroupMembership.objects.select_related('member')
            ),
            'grouptype'
        ).filter(begin_date__lte=date(int(year), 12, 31), end_date__gte=date(int(year), 1, 1), num_members__gt=0)

    def year_ordered_and_counts(self, year):
        queryset = self.year(year)
        gm_counts = queryset.aggregate(total=Count('memberships__member__id'), unique=Count('memberships__member__id', distinct=True))
        l = list(queryset)
        Group.order_by(l, 'name')
        return l, gm_counts['total'], gm_counts['unique']

class Group(SuperClass):
    objects = GroupManager()
    grouptype = models.ForeignKey("GroupType", on_delete=models.CASCADE, related_name="groups")
    begin_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f'{self.grouptype}: {self.begin_date} - {self.end_date}'

    @property
    def n_members(self):
        if hasattr(self, 'num_members'):
            return self.num_members
        return self.memberships.count()

    @property
    def duration(self):
        return Duration(self.begin_date, self.end_date)

    @property
    def memberships_by_member(self):
        l = list(self.memberships.all())
        GroupMembership.order_by(l, 'member')
        return l

    @classmethod
    def order_by(cls, groups_list, by, reverse=False):
        if by == 'date':
            key = attrgetter('end_date', 'begin_date')
        elif by == 'name':
            key = lambda g: strxfrm(g.grouptype.name)
        else:
            return
        groups_list.sort(key=key, reverse=reverse)

class GroupTypeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            count=Count('groups', distinct=True),
            count_non_empty=Count('groups', distinct=True, filter=Q(groups__memberships__gt=0)),
            count_members_total=Count('groups__memberships'),
            count_members_unique=Count('groups__memberships__member', distinct=True),
        )

    def all_by_name(self):
        l = list(self.get_queryset())
        GroupType.order_by(l, 'name')
        return l

    def get_prefetched_or_404(self, group_type_id):
        '''
        This is done in 3 queries:
        1. SELECT GroupType WHERE id=group_type_id
        2. SELECT Group WHERE grouptype__id=group_type_id
        3. SELECT GroupMembership WHERE group__id IN ^
        '''
        queryset = GroupType.objects.prefetch_related(
            Prefetch('groups', queryset=Group.objects.all()),
            Prefetch('groups__memberships', queryset=GroupMembership.objects.select_related('member')),
        )
        return get_object_or_404(queryset, id=group_type_id)

class GroupType(SuperClass):
    objects = GroupTypeManager()
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)
    comment = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    @property
    def n_groups(self):
        if hasattr(self, 'count'):
            return self.count
        return self.groups.count()

    @property
    def n_members_total(self):
        if hasattr(self, 'count_members_total'):
            return self.count_members_total
        return self.groups.aggregate(count=Count('memberships'))['count']

    @property
    def n_members_unique(self):
        if hasattr(self, 'count_members_unique'):
            return self.count_members_unique
        return self.groups.aggregate(count=Count('memberships__member', distinct=True))['count']

    @property
    def groups_by_date(self):
        l = list(self.groups.all())
        Group.order_by(l, 'date', True)
        return l

    @classmethod
    def order_by(cls, grouptypes_list, by, reverse=False):
        if by == 'name':
            key = lambda gt: strxfrm(gt.name)
        else:
            return
        grouptypes_list.sort(key=key, reverse=reverse)


class FunctionaryManager(models.Manager):
    def all_with_related(self):
        return self.get_queryset().select_related('functionarytype', 'member')

    def year(self, year):
        return self.all_with_related().filter(begin_date__lte=date(int(year), 12, 31), end_date__gte=date(int(year), 1, 1))

    def year_ordered_and_unique(self, year):
        queryset = self.year(year)
        unique_count = queryset.aggregate(count=Count('member__id', distinct=True))['count']
        l = list(queryset)
        Functionary.order_by(l, 'member')
        Functionary.order_by(l, 'date')
        Functionary.order_by(l, 'name')
        return l, unique_count

class Functionary(SuperClass):
    objects = FunctionaryManager()
    member = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="functionaries")
    functionarytype = models.ForeignKey("FunctionaryType", on_delete=models.CASCADE, related_name="functionaries")
    begin_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = (("member", "functionarytype", "begin_date", "end_date"),)

    def __str__(self):
        return f'{self.functionarytype}: {self.begin_date} - {self.end_date}, {self.member}'

    @property
    def duration(self):
        return Duration(self.begin_date, self.end_date)

    @classmethod
    def order_by(cls, functionaries_list, by, reverse=False):
        if by == 'date':
            key = attrgetter('end_date', 'begin_date')
        elif by == 'name':
            key = lambda f: strxfrm(f.functionarytype.name)
        elif by == 'member':
            key = lambda f: strxfrm(f.member.full_name_for_sorting)
        else:
            return
        functionaries_list.sort(key=key, reverse=reverse)

class FunctionaryTypeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            count=Count('functionaries'),
            count_unique=Count('functionaries__member', distinct=True),
        )

    def all_by_name(self):
        l = list(self.get_queryset())
        FunctionaryType.order_by(l, 'name')
        return l

    def get_prefetched_or_404(self, functionary_type_id):
        '''
        This is done in 2 queries:
        1. SELECT FunctionaryType WHERE id=functionary_type_id
        2. SELECT Functionary WHERE functionarytype__id=functionary_type_id
        '''
        queryset = FunctionaryType.objects.prefetch_related(
            Prefetch('functionaries', queryset=Functionary.objects.select_related('member')),
        )
        return get_object_or_404(queryset, id=functionary_type_id)

class FunctionaryType(SuperClass):
    objects = FunctionaryTypeManager()
    name = models.CharField(max_length=64, blank=False, null=False, unique=True)
    comment = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    @property
    def n_functionaries_total(self):
        if hasattr(self, 'count'):
            return self.count
        return self.functionaries.count()

    @property
    def n_functionaries_unique(self):
        if hasattr(self, 'count_unique'):
            return self.count_unique
        return self.functionaries.aggregate(count=Count('member', distinct=True))['count']

    @property
    def functionaries_by_date(self):
        l = list(self.functionaries.all())
        Functionary.order_by(l, 'member')
        Functionary.order_by(l, 'date', True)
        return l

    @classmethod
    def order_by(cls, functionarytypes_list, by, reverse=False):
        if by == 'name':
            key = lambda ft: strxfrm(ft.name)
        else:
            return
        functionarytypes_list.sort(key=key, reverse=reverse)


class MemberTypeManager(models.Manager):
    def all_with_related(self):
        return self.get_queryset().select_related('member')

    def begin_year(self, year):
        return self.all_with_related().filter(begin_date__year=year)

    def ordinary_members_begin_year(self, year):
        return self.begin_year(year).filter(type='OM')

    def ordinary_members_begin_year_ordered(self, year):
        l = list(self.ordinary_members_begin_year(year))
        MemberType.order_by(l, 'member')
        return l

    def stalms_begin_year(self, year):
        return self.begin_year(year).filter(type='ST')

    def stalms_begin_year_ordered(self, year):
        l = list(self.stalms_begin_year(year))
        MemberType.order_by(l, 'member')
        return l

class MemberType(SuperClass):
    objects = MemberTypeManager()
    TYPES = (
        ("PH", "Phux"),
        ("OM", "Ordinarie Medlem"),
        ("JS", "JuniorStÄlM"),
        ("ST", "StÄlM"),
        ("FG", "Färdig"),
        ("EM", "Ej längre medlem"),
        ("VP", "Viktig person"),
        ("KA", "Kanslist"),
        ("IM", "Inte medlem"),
        ("KE", "Kanslist emerita"),

    )
    member = models.ForeignKey("Member", on_delete=models.CASCADE, related_name='member_types')
    begin_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    type = models.CharField(max_length=2, choices=TYPES, default="PH")

    def __str__(self):
        s = f'{self.get_type_display()}: {self.begin_date} -'
        s += f' {self.end_date}' if self.end_date else '>'
        return s

    @classmethod
    def order_by(cls, membertypes_list, by, reverse=False):
        if by == 'begin_date':
            key = lambda mt: mt.begin_date
        elif by == 'end_date':
            key = lambda mt: mt.end_date or date(9999, 12, 31)
        elif by == 'member':
            key = lambda mt: strxfrm(mt.member.full_name_for_sorting)
        else:
            return
        membertypes_list.sort(key=key, reverse=reverse)
