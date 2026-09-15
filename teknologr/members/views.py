from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from members.models import *
from members.forms import *
from members.programmes import DEGREE_PROGRAMME_CHOICES
from registration.models import Applicant
from registration.forms import RegistrationForm
from api.ldap import LDAPAccountManager, LDAPError_to_string
import api.bill as bill
from getenv import env
from locale import strxfrm
from ldap import LDAPError


def set_context_side(context, category, active_obj=None):
    side = {}
    side['active'] = category
    side['active_obj'] = active_obj.id if active_obj else None
    side['new_button'] = True
    if category == 'members':
        side['sname'] = 'medlem'
        side['form'] = MemberForm(initial={'given_names': '', 'surname': ''}, auto_id="mmodal_%s")
        # XXX: Duplicated in MemberLookup.get_query for when the search box is emptied
        side['objects'] = Member.objects.order_by('-modified')[:50]
        # Add the active member to the list if it is not there already
        if active_obj and active_obj not in side['objects']:
            from itertools import chain
            side['objects'] = list(chain([active_obj], side['objects']))
        side['objects'] = [{'id': m.id, 'name': m.get_full_name_HTML()} for m in side['objects']]
    elif category == 'grouptypes':
        side['sname'] = 'grupp'
        side['form'] = GroupTypeForm(auto_id="gtmodal_%s")
        side['objects'] = GroupType.objects.all_by_name()
    elif category == 'functionarytypes':
        side['sname'] = 'post'
        side['form'] = FunctionaryTypeForm(auto_id="ftmodal_%s")
        side['objects'] = FunctionaryType.objects.all_by_name()
    elif category == 'decorations':
        side['sname'] = 'betygelse'
        side['form'] = DecorationForm(auto_id="dmodal_%s")
        side['objects'] = Decoration.objects.all_by_name()
    elif category == 'applicants':
        side['sname'] = 'ansökning'
        side['objects'] = Applicant.objects.order_by('-created_at')
        side['new_button'] = False
        side['applicant_tool_icons'] = True
        side['multiple_applicants_form'] = MultipleApplicantAdditionForm()

    context['side'] = side

    # XXX: Is not part of the side context, but this is a convenient place to define it. Could change the function name to something like set/get_default_context instead.
    context['info_url'] = env('INFO_URL')


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def empty(request, category):
    context = {}
    set_context_side(context, category)
    return render(request, 'base.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def member(request, member_id):
    '''
    This is done in 10 queries:
      1-5. Fetch Member with prefetched and ordered fields
      6. SELECT Decoration (for form drop-down list)
      7. SELECT FunctionaryType (for form drop-down list)
      8-9. SELECT Group WHERE not_already_member (for form drop-down list)
      10. SELECT Member (for side bar)
    '''
    context = {}
    member = Member.objects.get_prefetched_or_404(member_id)
    context['member'] = member

    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            try:
                form.save()
            except LDAPError as e:
                form.add_error('email', f'Could not sync to LDAP: {LDAPError_to_string(e)}')
            context['result'] = 'success'
        else:
            context['result'] = 'failure'
    else:
        form = MemberForm(instance=member)

    context['programmes'] = [
        programme
        for school, programmes in DEGREE_PROGRAMME_CHOICES.items()
        for programme in programmes
    ]
    context['programmes'].sort(key=lambda p: strxfrm(p))

    context['form'] = form
    context['full_name'] = member.full_name

    # Get decorations
    context['decoration_ownerships'] = member.decoration_ownerships_by_date
    context['add_do_form'] = DecorationOwnershipForm(initial={'member': member_id})

    # Get functionary positions
    context['functionaries'] = member.functionaries_by_date
    context['add_f_form'] = FunctionaryForm(initial={'member': member_id})

    # Get groups
    context['group_memberships'] = member.group_memberships_by_date
    context['add_gm_form'] = GroupMembershipForm(initial={'member': member_id})

    # Get membertypes
    context['membertypes'] = member.member_types.all()
    context['add_mt_form'] = MemberTypeForm(initial={'member': member_id})

    # Get LDAP and BILL account info based on the username
    if member.username:
        try:
            with LDAPAccountManager() as lm:
                context['LDAP'] = lm.get_user_details(member.username)
        except LDAPError as e:
            context['LDAP'] = {'error': LDAPError_to_string(e)}

        try:
            info = bill.get_account(member.username)
            if info:
                context['BILL'] = info
                context['bill_admin_url'] = bill.admin_url(info.get('acc'))
        except bill.BILLException as e:
            context['BILL'] = {'error': str(e)}

        gk = context['generikey'] = {}
        try:
            gk['key'] = bill.get_key(member.username)
        except bill.BILLException as e:
            gk['error'] = str(e)

    # load side list items
    set_context_side(context, 'members', member)
    return render(request, 'member.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def membertype_form(request, membertype_id):
    membertype = get_object_or_404(MemberType, id=membertype_id)
    return render(request, 'forms/membertype.html', {
        'form': MemberTypeForm(instance=membertype),
        'formid': 'edit-mt-form'
    })


def set_context_gt(context, gtid, prefetch_memberships=False):
    gt = context['grouptype'] = GroupType.objects.get_prefetched_or_404(gtid, prefetch_memberships)
    context['groups'] = gt.groups_by_date
    context['edit_gt_form'] = GroupTypeForm(instance=gt)
    context['add_g_form'] = GroupForm(initial={"grouptype": gtid})
    return gt

def set_context_g(context, gid):
    gid = int(gid)
    if 'groups' in context:
        g = context['group'] = next((group for group in context['groups'] if group.id == gid), None)
        if not g:
            raise Http404('No Group matches the given query.')
    else:
        g = context['group'] = Group.objects.get_prefetched_or_404(gid, False)

    context['groupmembers'] = g.memberships_by_member
    context['edit_g_form'] = GroupForm(instance=g)
    # context['add_gm_form'] = GroupMembershipForm(initial={"group": gid})
    context['emails'] = "\n".join(
        [membership.member.email for membership in context['groupmembers']]
    )
    return g

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def group_type_content(request, gtid):
    context = {}
    set_context_gt(context, gtid)
    return render(request, 'group_type.html', context)

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def group_content(request, gtid, gid):
    context = {}
    g = set_context_g(context, gid)

    # Check GroupType id without fetching the related object
    if g.grouptype_id != int(gtid):
        raise Http404('Group does not belong to the given GroupType.')

    return render(request, 'group.html', context)

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def group_type(request, gtid, gid=None):
    '''
    Could probably be enhanced to not query for memberships if no group_id is given, because currently 4 queries are done no matter what:
      1-3. Fetch GroupType with prefetched and ordered fields
      4. SELECT GroupType (for side bar)
    '''
    context = {}
    gt = set_context_gt(context, gtid, gid is not None)
    if gid is not None:
        set_context_g(context, gid)
    set_context_side(context, 'grouptypes', gt)
    return render(request, 'group_type_full.html', context)


def set_context_ft(context, ft_id):
    ft = context['functionary_type'] = FunctionaryType.objects.get_prefetched_or_404(ft_id)
    context['functionaries'] = ft.functionaries_by_date
    context['edit_ft_form'] = FunctionaryTypeForm(instance=ft)
    context['add_f_form'] = FunctionaryForm(initial={"functionarytype": ft_id})
    return ft

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def functionary_type_content(request, ft_id):
    context = {}
    set_context_ft(context, ft_id)
    return render(request, 'functionary_type.html', context)

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def functionary_type(request, ft_id):
    '''
    This is done in 3 queries:
      1-2. Fetch FunctionaryType with prefetched and ordered fields
      3. SELECT FunctionaryType (for side bar)
    '''
    context = {}
    ft = set_context_ft(context, ft_id)
    set_context_side(context, 'functionarytypes', ft)
    return render(request, 'functionary_type_full.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def functionary_form(request, f_id):
    functionary = get_object_or_404(Functionary, id=f_id)
    return render(request, 'forms/functionary.html', {
        'form': FunctionaryForm(instance=functionary),
    })


def set_context_d(context, d_id):
    d = context['decoration'] = Decoration.objects.get_prefetched_or_404(d_id)
    context['decoration_ownerships'] = d.ownerships_by_date
    context['edit_d_form'] = DecorationForm(instance=d)
    context['add_do_form'] = DecorationOwnershipForm(initial={"decoration": d_id})
    return d

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def decoration_content(request, d_id):
    context = {}
    set_context_d(context, d_id)
    return render(request, 'decoration.html', context)

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def decoration(request, d_id):
    '''
    This is done in 3 queries:
      1-2. Fetch Decoration with prefetched and ordered fields
      3. SELECT Decoration (for side bar)
    '''
    context = {}
    d = set_context_d(context, d_id)
    set_context_side(context, 'decorations', d)
    return render(request, 'decoration_full.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def decoration_ownership_form(request, decration_ownership_id):
    decoration_ownership = get_object_or_404(DecorationOwnership, id=decration_ownership_id)
    return render(request, 'forms/decorationownership.html', {
        'form': DecorationOwnershipForm(instance=decoration_ownership),
        'form_id': 'edit-do-form',
    })


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def applicant(request, applicant_id):
    context = {}

    applicant = get_object_or_404(Applicant, id=applicant_id)

    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=applicant)
        if form.is_valid():
            form.save()
    else:
        form = RegistrationForm(instance=applicant)

    context['applicant'] = applicant
    context['form'] = form
    context['make_member_form'] = ApplicantAdditionForm()

    set_context_side(context, 'applicants', applicant)
    return render(request, 'applicant.html', context)
