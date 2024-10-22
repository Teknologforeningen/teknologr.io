from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.functions import TruncYear
from members.models import *
from members.utils import *
from katalogen.forms import EditProfileForm
from katalogen.utils import *
from django.db.models import Q, Count
from functools import reduce
from operator import and_
from collections import defaultdict
from ldap import LDAPError

def own_profile_or_403(request, member):
    '''
    Function for checking if the logged in user is a certain Member.
    '''
    if request.user.username != member.username:
        raise PermissionDenied()

def _get_base_context(request):
    return {
        'abc': "ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖ",
        'is_staff': request.user.is_staff if request else False,
    }


@login_required
def home(request):
    context = _get_base_context(request)
    context['home'] = True
    return render(request, 'browse.html', context)


@login_required
def search(request):
    result = Member.objects.search_by_name(request.GET.get('q').split())
    if len(result) == 1:
        return redirect('katalogen:profile', result[0].id)

    Member.order_by(result, 'name')

    return render(request, 'browse.html', {
        **_get_base_context(request),
        'members': result,
    })


@login_required
def profile(request, member_id):
    """
    View the public profile of a member. All details will be shown if the user allows it, or if this is the user's own profile.

    URL query parameters available:
     - combine=<0/1>: Whether or not to combine the same Functionaries and GroupMemberships into a single row. The ordering will switch to lexicographical instead of reversed date as well.
    """
    member = Member.objects.get_prefetched_or_404(member_id)
    functionaries = list(member.functionaries.all())
    group_memberships = list(member.group_memberships.all())

    combine = request.GET.get('combine', '0') != '0'

    # Order the items differently depending on if they will be combined or not
    ordering = [('name', False)] if combine else [('name', False), ('date', True)]
    for by, reverse in ordering:
        Functionary.order_by(functionaries, by, reverse)
        GroupMembership.order_by(group_memberships, by, reverse)

    ft_durations = [(f.functionarytype, f.duration) for f in functionaries]
    gt_durations = [(gm.group.grouptype, gm.group.duration) for gm in group_memberships]

    if combine:
        ft_durations = MultiDuration.combine_per_key(ft_durations)
        gt_durations = MultiDuration.combine_per_key(gt_durations)

    own_profile = member.username == request.user.username
    bill_balance = None
    if own_profile:
        bill_balance = member.get_bill_balance()

    return render(request, 'profile.html', {
        **_get_base_context(request),
        # XXX: Could use MemberSerializerPartial to remove any unwanted fields for real instead of just not showing them
        'own_profile': own_profile,
        'show_contact_info': own_profile or member.show_contact_info(),
        'member': member,
        'bill_balance': bill_balance,
        'combined': combine,
        'functionary_type_durations': ft_durations,
        'group_type_durations': gt_durations,
        'decoration_ownerships': member.decoration_ownerships_by_date,
    })

@login_required
def profile_info(request, member_id):
    """
    Only render the member information section, not the decorations etc., so no need to prefetch the extra info.
    """

    member = get_object_or_404(Member, id=member_id)
    own_profile = member.username == request.user.username

    return render(request, 'profile_information.html', {
        'own_profile': own_profile,
        'show_contact_info': own_profile or member.show_contact_info(),
        'member': member,
    })

@login_required
def profile_edit(request, member_id):
    """
    Update the member information. This can only be done by the user himself. Returns only the HTML for the member information, not the decorations etc. This makes it possible for HTMX to swap only part of the page when saving the info.
    """

    member = Member.objects.get_prefetched_or_404(member_id)
    own_profile_or_403(request, member)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=member)
        if form.is_valid():
            try:
                form.save()
                form = None
            except LDAPError:
                form.add_error('email', 'E-postadressen kunde tyvärr inte uppdateras, vänligen kontakta en administratör')
    else:
        form = EditProfileForm(instance=member)

    # XXX: Due to the "public name" in the header depends on whether or contact information is shared, it might happen that the header need to be updated if the user changes his settings... This does not happen currently.

    return render(request, 'profile_information.html', {
        'form': form,
        'own_profile': True,
        'show_contact_info': True,
        'member': member,
    })

@login_required
def startswith(request, letter):
    # Surname prefixes should be ignored

    # All filtering could be done here on the Python side, but letting the database pre-filter the members is probably more effective
    members = Member.objects.filter(Q(surname__istartswith=letter) | Q(surname__icontains=f' {letter}'))

    # Checking the surname without prefix
    members = [m for m in list(members) if m.get_surname_without_prefixes()[0].upper() == letter.upper()]
    Member.order_by(members, 'name')

    return render(request, 'browse.html', {
        **_get_base_context(request),
        'members': members,
    })


@login_required
def myprofile(request):
    member = get_object_or_404(Member, username=request.user.username)
    return redirect('katalogen:profile', member.id)


@login_required
def decorations(request):
    # XXX: More info:
    #  - Date of first/latest?
    return render(request, 'decorations.html', {
        **_get_base_context(request),
        'decorations': Decoration.objects.all_by_name(),
    })


@login_required
def decoration(request, decoration_id):
    decoration = Decoration.objects.get_prefetched_or_404(decoration_id)
    decoration_ownerships = decoration.ownerships_by_date

    return render(request, 'decoration_ownerships.html', {
        **_get_base_context(request),
        'decoration': decoration,
        'decoration_ownerships': decoration_ownerships,
    })


@login_required
def functionary_types(request):
    # XXX: More info:
    #  - Date of first/latest?
    return render(request, 'functionary_types.html', {
        **_get_base_context(request),
        'functionary_types': FunctionaryType.objects.all_by_name(),
    })


@login_required
def functionary_type(request, functionary_type_id):
    """
    List all Functionaries of a certain FunctionaryType. The functionaries will be ordered in reverse date order by default.

    URL query parameters available:
     - combine=<0/1>: Whether or not to combine overlapping Functionaries of the same Member into a single row.
    """
    functionary_type = FunctionaryType.objects.get_prefetched_or_404(functionary_type_id)
    functionaries = list(functionary_type.functionaries.all())

    durations = [(f.member, f.duration) for f in functionaries]

    combine = request.GET.get('combine', '0') != '0'
    if combine:
        durations = MultiDuration.combine_per_key(durations)

    # Sort the pairs by date and member name by default
    durations.sort(key=lambda pair: (pair[1], pair[0].public_full_name_for_sorting), reverse=True)

    return render(request, 'functionaries.html', {
        **_get_base_context(request),
        'functionary_type': functionary_type,
        'functionary_durations': durations,
        'combined': combine,
    })


@login_required
def group_types(request):
    # XXX: More info:
    #  - Date of first/latest?
    return render(request, 'group_types.html', {
        **_get_base_context(request),
        'group_types': GroupType.objects.all_by_name(),
    })


@login_required
def groups(request, group_type_id):
    group_type = GroupType.objects.get_prefetched_or_404(group_type_id)

    # Do not want to display empty groups here, but filtering that in the template instead of the query

    return render(request, 'groups.html', {
        **_get_base_context(request),
        'group_type': group_type,
        'groups': group_type.groups_by_date,
    })


@login_required
def group_memberships(request, group_type_id):
    group_type = GroupType.objects.get_prefetched_or_404(group_type_id)

    durations = [(gm.member, g.duration) for g in group_type.groups.all() for gm in g.memberships.all()]

    # Combine all durations for each Member
    durations = MultiDuration.combine_per_key(durations)

    # Sort the pairs by member name by default
    durations.sort(key=lambda pair: (pair[0].public_full_name_for_sorting))

    return render(request, 'group_memberships.html', {
        **_get_base_context(request),
        'group_type': group_type,
        'group_membership_durations': durations,
    })


@login_required
def years(request):
    '''
    This is done in 4 queries, as you would expect by reading the code:
      1. SELECT Functionary => COUNT
      2. SELECT GroupMembership => COUNT
      3. SELECT DecortaionOwnership => COUNT
      4. SELECT MemberType WHERE type IN ["OM", "ST"] => COUNT
    '''
    years = defaultdict(dict)

    def add(obj, key, count_key=None):
        date = obj['year']
        if date is None:
            return

        y = date.year
        years[y][key] = obj[count_key or key]

    # Get all functionaries and group them by their start year, and for each year return a count for the total amount of functionaries and the amount of unique members holding the posts
    # XXX: This does not include all valid date intervals
    f_counts = Functionary.objects.annotate(year=TruncYear('begin_date')).values('year').annotate(functionaries_total=Count('id'), functionaries_unique=Count('member__id', distinct=True)).values('year', 'functionaries_total', 'functionaries_unique')
    for obj in f_counts:
        add(obj, 'functionaries_total')
        add(obj, 'functionaries_unique')

    # Get groups and group them by their start year, and for each year return a count for the total amount of groups, the total amount of members in the groups, and the amount of unique members holding in the groups
    # XXX: This does not include all valid date intervals
    gm_counts = GroupMembership.objects.annotate(year=TruncYear('group__begin_date')).values('year').annotate(groups=Count('group', distinct=True), group_memberships_total=Count('member'), group_memberships_unique=Count('member', distinct=True)).values('year', 'groups', 'group_memberships_total', 'group_memberships_unique')
    for obj in gm_counts:
        add(obj, 'groups')
        add(obj, 'group_memberships_total')
        add(obj, 'group_memberships_unique')

    # Get all decorations and group them by the year they were aquired, and return a count for each year
    do_counts = DecorationOwnership.objects.annotate(year=TruncYear('acquired')).values('year').annotate(decoration_ownerships=Count('id')).values('year', 'decoration_ownerships')
    for obj in do_counts:
        add(obj, 'decoration_ownerships')

    # Get all StÄlMs and ordinary members and group them by the year they became members, and return a count for each type/year combination
    m_counts = MemberType.objects.filter(Q(type='OM') | Q(type='ST')).annotate(year=TruncYear('begin_date')).values('year', 'type').annotate(members=Count('member')).values('year', 'type', 'members')
    for obj in m_counts:
        add(obj, 'members_ordinary' if obj['type'] == 'OM' else 'members_stalm', 'members')

    return render(request, 'years.html', {
        **_get_base_context(request),
        'years': dict(sorted(years.items(), reverse=True)),
    })

@login_required
def year(request, year):
    if int(year) <= 0:
        return render(request, 'year.html', {
            **_get_base_context(request),
            'year': year,
        })

    '''
    This could be enhanced, but curretnly it is done with 10 queries:
      1. SELECT Functionary WHERE correct_year => COUNT
      2. SELECT Functionary WHERE correct_year
      3. SELECT GroupMembership WHERE correct_year => COUNT
      4. COUNT DISTINCT over ^
      5. group_ids, group_type_ids = SELECT Group WHERE correct_year
      6. SELECT GroupMembership WHERE group__id IN group_ids
      7. SELECT GroupType WHERE id IN group_type_ids
      8. SELECT DecortaionOwnership WHERE correct_year
      9. SELECT MemberType WHERE correct_year AND type="OM"
      10. SELECT MemberType WHERE correct_year AND type="ST"
    '''

    # Get all functionaries for the year
    functionaries, functionaries_unique_count = Functionary.objects.year_ordered_and_unique(year)

    # Get all groups and group memberships for the year
    groups, group_memberships_total, group_memberships_unique = Group.objects.year_ordered_and_counts(year)

    return render(request, 'year.html', {
        **_get_base_context(request),
        'year': year,
        'decoration_ownerships': DecorationOwnership.objects.year_ordered(year),
        'functionaries': functionaries,
        'functionaries_unique_count': functionaries_unique_count,
        'groups': groups,
        'group_memberships_total': group_memberships_total,
        'group_memberships_unique': group_memberships_unique,
        'member_types_ordinary': MemberType.objects.ordinary_members_begin_year_ordered(year),
        'member_types_stalm': MemberType.objects.stalms_begin_year_ordered(year),
    })
