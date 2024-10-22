import django_filters
from django.db.models import Count
from members.models import *
from functools import reduce
from operator import and_

class BooleanFilter(django_filters.BooleanFilter):
    '''
    The default null label is for some reason 'unknown', but I want it to be ''
    '''
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = django_filters.widgets.BooleanWidget
        super().__init__(*args, **kwargs)

class CharFilterWithKeywords(django_filters.CharFilter):
    '''
    Take a CharFilter. You can filter on a specific phrase or leave it empty, but what if you want to filter null/empty values? This filter applies predetermined null/~null filters if the value is a certain keyword:
        - '-' => isnull=True
        - '*' => isnull=False

    Not suitable for fields where the keywords are possible values, and does not apply if the 'method' argument is given in the constructor.
    '''

    def filter(self, qs, value):
        q = Q(**{f'{self.field_name}__isnull': True}) | Q(**{f'{self.field_name}__exact': ''})
        if value == '-':
            return qs.filter(q)
        if value == '*':
            return qs.exclude(q)
        return super().filter(qs, value)


class BaseFilter(django_filters.rest_framework.FilterSet):
    '''
    Base filter class that takes care of normal users from using staff-only filters.
    '''
    STAFF_ONLY = []
    created = django_filters.DateFromToRangeFilter(label='Skapad mellan')
    modified = django_filters.DateFromToRangeFilter(label='Modifierad mellan')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        always_last = []
        # Inherited classes can remove these fields, so need to check for that
        if not hasattr(self, 'created') or self.created:
            always_last.append('created')
        if not hasattr(self, 'modified') or self.modified:
            always_last.append('modified')

        # Handle thie special case STAFF_ONLY = '__all__'
        if self.STAFF_ONLY == '__all__':
            self.STAFF_ONLY = [k for k in list(self.filters.keys()) if k not in always_last]
        self.STAFF_ONLY = self.STAFF_ONLY + always_last

        # If normal user, remove all staff-only filters, otherwise move them last and add a prefix to their labels
        is_staff = self.is_staff
        for key in self.STAFF_ONLY:
            f = self.filters.pop(key)
            if is_staff:
                f.label = f'[Staff only] {f.label}'
                self.filters[key] = f

    @property
    def is_staff(self):
        ''' Helper method for checking if the user making the request is staff '''
        user = self.request.user
        return user and user.is_staff

    def filter_count(self, queryset, value, field_name):
        name = f'n_{field_name}'
        queryset = queryset.annotate(**{name: Count(field_name, distinct=True)})
        min = value.start
        max = value.stop
        if min is not None:
            queryset = queryset.exclude(**{f'{name}__lt': min})
        if max is not None:
            queryset = queryset.exclude(**{f'{name}__gt': max})
        return queryset


class MemberFilter(BaseFilter):
    '''
    A custom FilterSet class that set up filters for Members. Some filters are ignored if the requesting user is not staff.
    '''

    # Public filters
    name = django_filters.CharFilter(
        # NOTE: Custom field name
        # NOTE: given_names is semi-public, handling of hidden Members is done in the method
        method='filter_name',
        label='Namnet innehåller',
    )
    n_functionaries = django_filters.RangeFilter(
        method='filter_n_functionaries',
        label='Antalet poster är mellan',
    )
    n_groups = django_filters.RangeFilter(
        method='filter_n_groups',
        label='Antalet grupper är mellan',
    )
    n_decorations = django_filters.RangeFilter(
        method='filter_n_decorations',
        label='Antalet betygelser är mellan',
    )
    degree_programme = CharFilterWithKeywords(
        lookup_expr='icontains',
        label='Studieprogrammet innehåller',
    )
    enrolment_year = django_filters.RangeFilter(
        label='Inskrivingsåret är mellan',
    )
    graduated = BooleanFilter(
        method='filter_graduated',
        label='Utexaminerad?',
    )
    graduated_year = django_filters.RangeFilter(
        label='Utexamineringsåret är mellan',
    )

    # Public but hidable fields (hidden Members are not included)
    HIDABLE = Member.HIDABLE_FIELDS + ['address']
    address = django_filters.CharFilter(
        # NOTE: Custom field name, but added manually to HIDABLE
        method='filter_address',
        label='Adressen innehåller',
    )
    email = CharFilterWithKeywords(
        lookup_expr='icontains',
        label='E-postadressen innehåller',
    )

    # Staff only filters
    STAFF_ONLY = Member.STAFF_ONLY_FIELDS
    birth_date = django_filters.DateFromToRangeFilter(
        label='Född mellan',
    )
    student_id = CharFilterWithKeywords(
        label='Studienummer',
    )
    dead = BooleanFilter(
        label='Avliden?',
    )
    subscribed_to_modulen = BooleanFilter(
        label='Prenumererar på Modulen?',
    )
    allow_studentbladet = BooleanFilter(
        label='Prenumererar på Studentbladet?',
    )
    allow_publish_info = BooleanFilter(
        label='Tillåter publicering av kontaktinformation?',
    )
    comment = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Kommentaren innehåller',
    )
    username = CharFilterWithKeywords(
        label='Användarnamn',
    )
    bill_code = CharFilterWithKeywords(
        label='BILL-konto',
    )

    def includes_hidable_field(self):
        ''' Check if the current query includes filtering on any hidable Member fields '''
        for name, value in self.data.items():
            # XXX: This wrongly identifies invalid filter values as being set. For example, providing an invalid string to a BooleanFilter field will be caught here, even though the field will not be filtered... Maybe this is good enough?
            if name in self.HIDABLE and any(value):
                return True
        return False

    def filter_queryset(self, queryset):
        ''' Remove hidden Members for normal users if filters on any hidden field is used. '''
        if not self.is_staff and self.includes_hidable_field():
            queryset = queryset.filter(Member.get_show_info_Q())
        return super().filter_queryset(queryset)

    def filter_name(self, queryset, name, value):
        '''
        The given_names field is semi-public so can not filter on that for hidden Members.
        '''
        is_staff = self.is_staff

        # Split the filter value and compare all individual values against all name columns
        queries = []
        for v in value.split():
            # XXX: The preferred name does not have to be set in the database, so hidden members with no preferred name set will not show up for normal users even if the derived preferred name would match
            q = Q(preferred_name__icontains=v) | Q(surname__icontains=v)
            # Non-staff users only get to filter on 'given_names' if the Member has allowed publishing of info
            if is_staff:
                q |= Q(given_names__icontains=v)
            else:
                q |= (Q(given_names__icontains=v) & Member.get_show_info_Q())
            queries.append(q)
        return queryset.filter(reduce(and_, queries))

    def filter_address(self, queryset, name, value):
        # Split the filter value and compare all individual values against all address columns
        queries = []
        for v in value.split():
            queries.append(
                Q(street_address__icontains=v) |
                Q(postal_code__icontains=v) |
                Q(city__icontains=v) |
                Q(country__icontains=v)
            )
        return queryset.filter(reduce(and_, queries))

    def filter_graduated(self, queryset, name, value):
        '''
        Modifying the graduated flag whan adding a graduated year can sometimes be forgotten, so taking that into consideration for this filter query.
        '''
        assert value in [True, False, None]

        if value:
            # Graduated or graduated year is set
            return queryset.filter(Q(graduated=True) | Q(graduated_year__isnull=False))
        # Not graduated and graduated year is not set
        return queryset.filter(Q(graduated=False) & Q(graduated_year__isnull=True))

    def filter_n_functionaries(self, queryset, name, value):
        return self.filter_count(queryset, value, 'functionaries')

    def filter_n_groups(self, queryset, name, value):
        return self.filter_count(queryset, value, 'group_memberships')

    def filter_n_decorations(self, queryset, name, value):
        return self.filter_count(queryset, value, 'decoration_ownerships')

class DecorationFilter(BaseFilter):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Betygelsens namn innehåller',
    )
    n_ownerships = django_filters.RangeFilter(
        method='filter_n_ownerships',
        label='Antalet innehavare är mellan',
    )

    def filter_n_ownerships(self, queryset, name, value):
        return self.filter_count(queryset, value, 'ownerships')

class DecorationOwnershipFilter(BaseFilter):
    decoration__id = django_filters.NumberFilter(label='Betygelsens id')
    decoration__name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Betygelsens namn innehåller',
    )
    member__id = django_filters.NumberFilter(label='Medlemmens id')
    acquired = django_filters.DateFromToRangeFilter(label='Tilldelat mellan')


class FunctionaryTypeFilter(BaseFilter):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Postens namn innehåller',
    )
    n_functionaries_total = django_filters.RangeFilter(
        method='filter_n_functionaries_total',
        label='Totala antalet postinnehavare är mellan',
    )
    # XXX: What about filtering on unique functionaries?

    def filter_n_functionaries_total(self, queryset, name, value):
        return self.filter_count(queryset, value, 'functionaries')

class FunctionaryFilter(BaseFilter):
    functionarytype__id = django_filters.NumberFilter(label='Postens id')
    functionarytype__name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Postens namn innehåller',
    )
    member__id = django_filters.NumberFilter(label='Medlemmens id')
    begin_date = django_filters.DateFromToRangeFilter(label='Startdatumet är mellan')
    end_date = django_filters.DateFromToRangeFilter(label='Slutdatumet är mellan')


class GroupTypeFilter(BaseFilter):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Gruppens namn innehåller',
    )
    n_groups = django_filters.RangeFilter(
        method='filter_n_groups',
        label='Antalet undergrupper är mellan',
    )
    # XXX: What about filtering on amount of members (total and unique)?

    def filter_n_groups(self, queryset, name, value):
        return self.filter_count(queryset, value, 'groups')

class GroupFilter(BaseFilter):
    begin_date = django_filters.DateFromToRangeFilter(label='Startdatumet är mellan')
    end_date = django_filters.DateFromToRangeFilter(label='Slutdatumet är mellan')
    grouptype__id = django_filters.NumberFilter(label='Gruppens id')
    grouptype__name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Gruppens namn innehåller',
    )
    n_members = django_filters.RangeFilter(
        method='filter_n_members',
        label='Antalet gruppmedlemmar är mellan',
    )

    def filter_n_members(self, queryset, name, value):
        return self.filter_count(queryset, value, 'memberships')

class GroupMembershipFilter(BaseFilter):
    group__id = django_filters.NumberFilter(label='Undergruppens id')
    group__begin_date = django_filters.DateFromToRangeFilter(label='Undergruppens startdatum är mellan')
    group__end_date = django_filters.DateFromToRangeFilter(label='Undergruppens slutdatum är mellan')
    group__grouptype__id = django_filters.NumberFilter(label='Gruppens id')
    group__grouptype__name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Gruppens namn innehåller',
    )
    member__id = django_filters.NumberFilter(label='Medlemmens id')


class MemberTypeFilter(BaseFilter):
    STAFF_ONLY = '__all__'
    begin_date = django_filters.DateFromToRangeFilter(label='Startdatumet är mellan')
    end_date = django_filters.DateFromToRangeFilter(label='Slutdatumet är mellan')
    type = django_filters.ChoiceFilter(choices=MemberType.TYPES, label='Medlemstyp')
    member__id = django_filters.NumberFilter(label='Medlemmens id')


class ApplicantFilter(MemberFilter):
    STAFF_ONLY = '__all__'

    # Need to remove all Member fields that do not exist on Applicant
    graduated = None
    graduated_year = None
    comment = None
    dead = None
    bill_code = None
    created = None
    modified = None
    n_functionaries = None
    n_groups = None
    n_decorations = None

    # Add all extra fields
    motivation = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Motiveringen innehåller',
    )
    mother_tongue = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Modersmålet innehåller',
    )
    created_at = django_filters.DateFromToRangeFilter(label='Ansökningsdatumet är mellan')
