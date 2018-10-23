from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from members.models import *
from members.forms import *
from members.programmes import DEGREE_PROGRAMME_CHOICES
import datetime


def getCurrentYear():
    return datetime.date.today().year


def getFirstDayOfCurrentYear():
    return datetime.date(getCurrentYear(), 1, 1)


def getLastDayOfCurrentYear():
    return datetime.date(getCurrentYear(), 12, 31)


def getCurrentDate():
    return datetime.datetime.now()


# Create your views here

def set_side_context(context, category, active_obj=None):
    side = {}
    side['active'] = category
    side['active_obj'] = active_obj
    if category == 'members':
        side['sname'] = 'medlem'
        side['newForm'] = MemberForm(initial={'given_names': '', 'surname': ''})
        objects = Member.objects.order_by('-modified')[:50]
        if active_obj:
            active = Member.objects.get(pk=active_obj)
            if active not in objects:
                from itertools import chain
                objects = list(chain([active], objects))
        side['objects'] = objects
    elif category == 'groups':
        side['sname'] = 'grupp'
        side['newForm'] = GroupTypeForm()
        side['objects'] = GroupType.objects.all()
    elif category == 'functionaries':
        side['sname'] = 'post'
        side['newForm'] = FunctionaryTypeForm()
        side['objects'] = FunctionaryType.objects.all()
    elif category == 'decorations':
        side['sname'] = 'betygelse'
        side['newForm'] = DecorationForm()
        side['objects'] = Decoration.objects.all()
    context['side'] = side


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def empty(request, category):
    context = {}
    set_side_context(context, category)
    return render(request, 'base.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def member(request, member_id):
    context = {}

    member = get_object_or_404(Member, id=member_id)
    context['member'] = member

    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            from ldap import LDAPError
            try:
                form.save()
            except LDAPError:
                form.add_error("email", "Could not sync to LDAP")
            context['result'] = 'success'
        else:
            context['result'] = 'failure'
    else:
        form = MemberForm(instance=member)

    context['programmes'] = DEGREE_PROGRAMME_CHOICES
    context['form'] = form
    context['full_name'] = member

    # Get functionary positions
    context['functionaries'] = Functionary.objects.filter(member__id=member_id)
    context['addfunctionaryform'] = FunctionaryForm(initial={'member': member_id})

    # Get groups
    context['groups'] = GroupMembership.objects.filter(member__id=member_id)
    context['addgroupform'] = GroupMembershipForm(initial={'member': member_id})

    # Get membertypes
    context['membertypes'] = MemberType.objects.filter(member__id=member_id)
    context['addmembertypeform'] = MemberTypeForm(initial={'member': member_id})

    # Get user account info
    from api.ldap import LDAPAccountManager
    from api.bill import BILLAccountManager, BILLException
    if member.username:
        try:
            with LDAPAccountManager() as lm:
                context['LDAP'] = {'groups': lm.get_ldap_groups(member.username)}
        except Exception:
            context['LDAP'] = "error"

    if member.bill_code:
        bm = BILLAccountManager()
        try:
            context['BILL'] = bm.get_bill_info(member.bill_code)
        except BILLException as e:
            context['BILL'] = {"error": str(e)}

    # load side list items
    set_side_context(context, 'members', member.id)
    return render(request, 'member.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def membertype_form(request, membertype_id):
    membertype = get_object_or_404(MemberType, id=membertype_id)
    form = MemberTypeForm(instance=membertype)
    context = {'form': form, 'formid': 'editmembertypeform'}
    return render(request, 'membertypeform.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def group(request, grouptype_id, group_id=None):
    context = {}

    grouptype = get_object_or_404(GroupType, id=grouptype_id)
    context['grouptype'] = grouptype

    form = GroupTypeForm(instance=grouptype)

    # Get groups of group type
    context['groups'] = Group.objects.filter(grouptype__id=grouptype_id).order_by('-begin_date')
    context['groupTypeForm'] = form

    context['addgroupform'] = GroupForm(initial={
        "grouptype": grouptype_id,
        "begin_date": getFirstDayOfCurrentYear(),
        "end_date": getLastDayOfCurrentYear()
    })

    if group_id is not None:
        group = get_object_or_404(Group, id=group_id)
        context['group'] = group
        context['groupform'] = GroupForm(instance=group)
        context['groupmembershipform'] = GroupMembershipForm(initial={"group": group_id})
        context['groupmembers'] = GroupMembership.objects.filter(group=group)
        context['emails'] = "\n".join([ membership.member.email for membership in context['groupmembers'] ])

    set_side_context(context, 'groups', grouptype.id)
    return render(request, 'group.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def functionary(request, functionarytype_id):
    context = {}

    functionarytype = get_object_or_404(FunctionaryType, id=functionarytype_id)
    context['functionaryType'] = functionarytype
    form = FunctionaryTypeForm(instance=functionarytype)

    # Get functionaries of functionary type
    context['functionaries'] = Functionary.objects.filter(
        functionarytype__id=functionarytype_id).order_by('-begin_date')
    context['functionaryTypeForm'] = form
    context['addfunctionaryform'] = FunctionaryForm(initial={
        "functionarytype": functionarytype_id,
        "begin_date": getFirstDayOfCurrentYear(),
        "end_date": getLastDayOfCurrentYear()
    })

    set_side_context(context, 'functionaries', functionarytype.id)
    return render(request, 'functionary.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def decoration(request, decoration_id):
    context = {}

    decoration = get_object_or_404(Decoration, id=decoration_id)
    context['decoration'] = decoration
    context['decorationform'] = DecorationForm(instance=decoration)

    # Get groups of group type
    context['decorations'] = DecorationOwnership.objects.filter(decoration__id=decoration_id).order_by('-acquired')
    context['adddecorationform'] = DecorationOwnershipForm(
        initial={"decoration": decoration_id, 'acquired': getCurrentDate()})

    set_side_context(context, 'decorations', decoration.id)
    return render(request, 'decoration.html', context)
