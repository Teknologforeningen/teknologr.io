from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db.utils import IntegrityError
from rest_framework import viewsets
from api.serializers import *
from rest_framework.views import APIView
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from members.models import GroupMembership, Member, Group
from members.programmes import DEGREE_PROGRAMME_CHOICES
from registration.models import Applicant
from api.ldap import LDAPAccountManager
from ldap import LDAPError
from api.bill import BILLAccountManager, BILLException
from rest_framework_csv import renderers as csv_renderer
from api.mailutils import mailNewPassword
from collections import defaultdict
from datetime import datetime

# Create your views here.

# ViewSets define the view behavior.

# Members


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


# Groups

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupTypeViewSet(viewsets.ModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer


@api_view(['POST'])
def memberListSave(request):
    gid = request.data.get('group')
    members = request.data.get('member').strip("|").split("|")

    for mid in members:
        # get_or_create is used to ignore duplicates
        GroupMembership.objects.get_or_create(member_id=int(mid), group_id=int(gid))

    return Response(status=200)


# Functionaries

class FunctionaryViewSet(viewsets.ModelViewSet):
    queryset = Functionary.objects.all()
    serializer_class = FunctionarySerializer


class FunctionaryTypeViewSet(viewsets.ModelViewSet):
    queryset = FunctionaryType.objects.all()
    serializer_class = FunctionaryTypeSerializer


# Decorations

class DecorationViewSet(viewsets.ModelViewSet):
    queryset = Decoration.objects.all()
    serializer_class = DecorationSerializer


class DecorationOwnershipViewSet(viewsets.ModelViewSet):
    queryset = DecorationOwnership.objects.all()
    serializer_class = DecorationOwnershipSerializer


# MemberTypes

class MemberTypeViewSet(viewsets.ModelViewSet):
    queryset = MemberType.objects.all()
    serializer_class = MemberTypeSerializer


# User accounts

class LDAPAccountView(APIView):
    def get(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)
        result = {}
        with LDAPAccountManager() as lm:
            try:
                result = {'username': member.username, 'groups': lm.get_ldap_groups(member.username)}
            except LDAPError as e:
                return Response(str(e), status=400)

        return Response(result, status=200)

    def post(self, request, member_id):
        # Create LDAP and BILL accounts for given user
        member = get_object_or_404(Member, id=member_id)
        username = request.data.get('username')
        password = request.data.get('password')
        mailToUser = request.data.get('mail_to_user')
        if not username or not password:
            return Response("username or password field missing", status=400)

        if member.username:
            return Response("Member already has LDAP account", status=400)

        with LDAPAccountManager() as lm:
            try:
                lm.add_account(member, username, password)
                if mailToUser:
                    status = mailNewPassword(member, password)
                    if not status:
                        return Response("Password changed, failed to send mail", status=500)
            except LDAPError as e:
                return Response(str(e), status=400)

        # Store account details
        member.username = username
        member.save()

        # TODO: Send mail to user to notify about new account?

        return Response(status=200)

    def delete(self, request, member_id):
        # Delete LDAP account for a given user
        member = get_object_or_404(Member, id=member_id)

        if not member.username:
            return Response("Member has no LDAP account", status=400)
        if member.bill_code:
            return Response("BILL account must be deleted first", status=400)

        with LDAPAccountManager() as lm:
            try:
                lm.delete_account(member.username)
            except LDAPError as e:
                return Response(str(e), status=400)

        # Delete account information from user in db
        member.username = None
        member.save()

        return Response(status=200)


@api_view(['POST'])
def change_ldap_password(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    password = request.data.get('password')
    mailToUser = request.data.get('mail_to_user')
    if not password:
        return Response("password field missing", status=400)

    with LDAPAccountManager() as lm:
        try:
            lm.change_password(member.username, password)
            if mailToUser:
                status = mailNewPassword(member, password)
                if not status:
                    return Response("Password changed, failed to send mail", status=500)
        except LDAPError as e:
            return Response(str(e), status=400)

    return Response(status=200)


class BILLAccountView(APIView):
    def get(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)

        if not member.bill_code:
            return Response("Member has no BILL account", status=400)

        bm = BILLAccountManager()
        try:
            result = bm.get_bill_info(member.bill_code)
        except BILLException as e:
            return Response(str(e), status=400)

        return Response(result, status=200)

    def post(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)

        if member.bill_code:
            return Response("BILL account already exists", status=400)
        if not member.username:
            return Response("LDAP account missing", status=400)

        bm = BILLAccountManager()
        try:
            bill_code = bm.create_bill_account(member.username)
        except BILLException as e:
            return Response(str(e), status=400)

        member.bill_code = bill_code
        member.save()

        return Response(status=200)

    def delete(self, request, member_id):
        member = get_object_or_404(Member, id=member_id)

        if not member.bill_code:
            return Response("Member has no BILL account", status=400)

        bm = BILLAccountManager()
        try:
            bm.delete_bill_account(member.bill_code)
        except BILLException as e:
            return Response(str(e), status=400)

        member.bill_code = None
        member.save()

        return Response(status=200)


# Registration/Applicant

class ApplicantViewSet(viewsets.ModelViewSet):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer


class ApplicantMembershipView(APIView):
    def post(self, request, applicant_id):
        applicant = get_object_or_404(Applicant, id=applicant_id)
        new_member = Member()

        # Copy all applicant fields to Member object (except primary key)
        for field in filter(lambda _: not _.primary_key, applicant._meta.fields):
            setattr(new_member, field.name, getattr(applicant, field.name))

        # Fix needed fields
        degree_programme = applicant.degree_programme.split('_')
        if len(degree_programme) == 2:
            school, programme = degree_programme
            if programme in DEGREE_PROGRAMME_CHOICES.get(school, []):
                new_member.degree_programme = programme

        try:
            # Saving a new member might fail (e.g. unique constraints)
            new_member.save()
            applicant.delete()
        except IntegrityError as err:
            return Response(str(err), status=400)

        # Add MemberTypes if set
        membership_date = request.data.get('membership_date')
        if membership_date:
            self._create_member_type(new_member, membership_date, 'OM')

        phux_date = request.data.get('phux_date')
        if phux_date:
            self._create_member_type(new_member, phux_date, 'PH')

        return Response(status=200)

    def _create_member_type(self, member, date, type):
        try:
            tmp_member_type = MemberType(member=member, begin_date=date, type=type)
            tmp_member_type.save()
        except:
            # FIXME: inform user that MemberType saving was not succesful
            pass


@api_view(['POST'])
def multiApplicantSubmission(request):
    applicants = request.data.get('applicant').strip('|').split('|')

    # Simulate a POST request to ApplicantMembershipView
    am_view = ApplicantMembershipView()
    for aid in applicants:
        # TODO: add notification to user if unsuccesful applicant saving
        am_view.post(request, aid)

    return Response(status=200)


# JSON API:s

# Used by BILL
@api_view(['GET'])
def memberTypesForMember(request, mode, query):

    try:
        if mode == 'username':
            member = Member.objects.get(username=query)
        elif mode == 'studynumber':
            member = Member.objects.get(student_id=query)
        else:
            return Response(status=400)
    except Member.DoesNotExist as e:
        return Response(status=200)

    membertypes = {}

    for e in MemberType.objects.filter(member=member):
        membertypes[e.type] = (str(e.begin_date), str(e.end_date))

    data = {
        "given_names": member.given_names.split(),
        "surname": member.surname,
        "nickname": "",
        "preferred_name": member.preferred_name,
        "membertypes": membertypes
    }

    return Response(data, status=200)


# Used by GeneriKey
@api_view(['GET'])
def membersByMemberType(request, membertype, field=None):
    member_pks = MemberType.objects.filter(type=membertype, end_date=None).values_list("member", flat=True)
    fld = "username" if field == "usernames" else "student_id"
    members = Member.objects.filter(pk__in=member_pks).values_list(fld, flat=True)
    return Response(members, status=200)


# Data for HTK
# JSON file including all necessary information for HTK, i.e. member's activity at TF
@api_view(['GET'])
def htkDump(request, member_id=None):
    def dumpMember(member):
        # Functionaries
        funcs = Functionary.objects.filter(member=member)
        func_list = []
        for func in funcs:
            func_str = "{}: {} > {}".format(
                func.functionarytype.name,
                func.begin_date,
                func.end_date
            )
            func_list.append(func_str)
        # Groups
        groups = GroupMembership.objects.filter(member=member)
        group_list = []
        for group in groups:
            group_str = "{}: {} > {}".format(
                group.group.grouptype.name,
                group.group.begin_date,
                group.group.end_date
            )
            group_list.append(group_str)
        # Membertypes
        types = MemberType.objects.filter(member=member)
        type_list = []
        for type in types:
            type_str = "{}: {} > {}".format(
                type.get_type_display(),
                type.begin_date,
                type.end_date
            )
            type_list.append(type_str)
        # Decorations
        decorations = DecorationOwnership.objects.filter(member=member)
        decoration_list = []
        for decoration in decorations:
            decoration_str = "{}: {}".format(
                decoration.decoration.name,
                decoration.acquired
            )
            decoration_list.append(decoration_str)

        return {
            "id": member.id,
            "name": member.full_name,
            "functionaries": func_list,
            "groups": group_list,
            "membertypes": type_list,
            "decorations": decoration_list
        }

    if member_id:
        member = get_object_or_404(Member, id=member_id)
        data = dumpMember(member)
    else:
        data = [dumpMember(member) for member in Member.objects.all()]

    dumpname = 'filename="HTKdump_{}.json'.format(datetime.today().date())
    return Response(
            data,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


# CSV-render class
class ModulenRenderer(csv_renderer.CSVRenderer):
    header = ['firstname', 'lastname', 'street_address', 'postal_code', 'city', 'country']


# List of addresses whom to post modulen to
@api_view(['GET'])
@renderer_classes((ModulenRenderer,))
def modulenDump(request):

    recipients = Member.objects.exclude(
            postal_code='02150'
        ).exclude(
            dead=True
        ).filter(
            subscribed_to_modulen=True
        )

    recipients = [x for x in recipients if x.isValidMember()]

    content = [{
        'firstname': recipient.given_names,
        'lastname': recipient.surname,
        'street_address': recipient.street_address,
        'postal_code': recipient.postal_code,
        'city': recipient.city,
        'country': recipient.country
        } for recipient in recipients]

    dumpname = 'filename="modulendump_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


class ActiveRenderer(csv_renderer.CSVRenderer):
    header = ['position', 'member']


# Lists all members that are active at the moment. These are members
# that are either functionaries right now or in a group that has an
# active mandate
@api_view(['GET'])
@renderer_classes((ActiveRenderer,))
def activeDump(request):
    now = datetime.now().date()
    content = []

    # Functionaries
    all_functionaries = Functionary.objects.filter(
        begin_date__lt=now,
        end_date__gt=now
    )
    for func in all_functionaries:
        content.append({
            'position': str(func.functionarytype),
            'member': ''
        })
        content.append({
            'position': '',
            'member': func.member._get_full_preferred_name()
        })

    # Groups
    groupmemberships = GroupMembership.objects.all()
    grouped_by_group = defaultdict(list)
    for membership in groupmemberships:
        if membership.group.begin_date < now and membership.group.end_date > now:
            grouped_by_group[membership.group].append(membership.member)
    for group, members in grouped_by_group.items():
        content.append({
            'position': str(group.grouptype),
            'member': ''
        })
        content.extend([{
            'position': '',
            'member': m._get_full_preferred_name()
        } for m in members])

    dumpname = 'filename="activedump_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


class FullRenderer(csv_renderer.CSVRenderer):
    header = [
        'id', 'given_names', 'preferred_name', 'surname', 'membertype',
        'street_address', 'postal_code', 'city', 'country', 'birth_date',
        'student_id', 'enrolment_year', 'graduated', 'graduated_year',
        'degree_programme', 'dead', 'phone', 'email', 'subscribed_to_modulen',
        'allow_publish_info', 'username', 'bill_code', 'comment', 'should_be_stalmed'
    ]


# "Fulldump". If you need some arbitrary bit of info this with some excel magic might do the trick.
# Preferably tough for all common needs implement a specific endpoint for it (like modulen or HTK)
# to save time in the long run.
@api_view(['GET'])
@renderer_classes((FullRenderer,))
def fullDump(request):

    members = Member.objects.exclude(dead=True)

    content = [{
        'id': member.id,
        'given_names': member.given_names,
        'preferred_name': member.preferred_name,
        'surname': member.surname,
        'membertype': str(member.getMostRecentMemberType()),
        'street_address': member.street_address,
        'postal_code': member.postal_code,
        'city': member.city,
        'country': member.country,
        'birth_date': member.birth_date,
        'student_id': member.student_id,
        'enrolment_year': member.enrolment_year,
        'graduated': member.graduated,
        'graduated_year': member.graduated_year,
        'degree_programme': member.degree_programme,
        'dead': member.dead,
        'phone': member.phone,
        'email': member.email,
        'subscribed_to_modulen': member.subscribed_to_modulen,
        'allow_publish_info': member.allow_publish_info,
        'username': member.username,
        'bill_code': member.bill_code,
        'comment': member.comment,
        'should_be_stalmed': member.shouldBeStalm()}
        for member in members]

    dumpname = 'filename="fulldump_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


class ArskRenderer(csv_renderer.CSVRenderer):
    header = ['name', 'surname', 'street_address', 'postal_code', 'city', 'country', 'associations']


# Dump for Årsfestkommittén, includes all members that should be posted invitations.
# These include: honor-members, all TFS 5 years back + exactly 10 years back, all counsels, all current functionaries
@api_view(['GET'])
@renderer_classes((ArskRenderer,))
def arskDump(request):
    tfs_low_range = 5
    current_year = datetime.now().year

    counsel_ids = [
            10,  # Affärsrådet (AR)
            9,   # Finansrådet (FR)
            12,  # De Äldres Råd (DÄR)
            44,  # Fastighets Rådet (FaR)
            19,  # Kontinuitets Rådet (KonRad)
    ]
    styrelse_id = 2  # Styrelsen
    honor_id = 3  # Hedersmedlemmar

    # All saved associations
    by_association = defaultdict(list)

    # Common query for checking if member is deceased
    is_alive = Q(member__dead=False)

    # Query for current counsel membership
    counsel_members_query = Q(group__grouptype__id__in=counsel_ids, group__begin_date__year__gte=current_year)

    # Query for board membership
    is_styrelse_q = Q(group__grouptype__id=styrelse_id)
    is_recent_q = Q(group__begin_date__year__gte=current_year-tfs_low_range, group__begin_date__year__lte=current_year)
    is_ten_years_back_q = Q(group__begin_date__year=current_year-10)
    styrelse_members_query = Q(is_styrelse_q & Q(is_recent_q | is_ten_years_back_q))

    # Apply membership queries to database and append answer
    memberships = GroupMembership.objects.filter(Q(styrelse_members_query | counsel_members_query) & is_alive)
    for membership in memberships:
        by_association[membership.member].append(str(membership.group))

    # Apply honor member queries and append answer
    honor_decoration = DecorationOwnership.objects.filter(Q(decoration__id=honor_id) & is_alive)
    for decoration in honor_decoration:
        by_association[decoration.member].append(decoration.decoration.name)

    # Apply functionary queries and append answer
    functionaries = Functionary.objects.filter(Q(begin_date__year=current_year) & is_alive)
    for functionary in functionaries:
        by_association[functionary.member].append(functionary.functionarytype.name)

    # Finally format the data correctly
    content = [{
        'name': member.given_names,
        'surname': member.surname,
        'street_address': member.street_address,
        'postal_code': member.postal_code,
        'city': member.city,
        'country': member.country.name,
        'associations': ','.join(association)}
        for member, association in by_association.items()]

    dumpname = 'filename="arskdump_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


class RegEmailRenderer(csv_renderer.CSVRenderer):
    header = ['name', 'surname', 'preferred_name', 'email']


# Dump for receiving all emails from member applicants
# Used by e.g. the PhuxMästare to send out information
@api_view(['GET'])
@renderer_classes((RegEmailRenderer,))
def regEmailDump(request):
    applicants = Applicant.objects.all()
    content = [{
        'name': applicant.given_names,
        'surname': applicant.surname,
        'preferred_name': applicant.preferred_name,
        'email': applicant.email}
        for applicant in applicants]

    dumpname = 'filename="regEmailDump_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


class ApplicantLanguagesRenderer(csv_renderer.CSVRenderer):
    header = ['language']


@api_view(['GET'])
@renderer_classes((ApplicantLanguagesRenderer,))
def applicantLanguages(request):
    applicants = Applicant.objects.exclude(Q(mother_tongue__isnull=True) | Q(mother_tongue__exact=''))
    content = [{
        'language': applicant.mother_tongue}
        for applicant in applicants]

    dumpname = 'filename="applicantLanguages_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )


# CSV-render class
class StudentbladetRenderer(csv_renderer.CSVRenderer):
    header = ['name', 'street_address', 'postal_code', 'city', 'country']


# List of addresses whom to post Studentbladet to
@api_view(['GET'])
@renderer_classes((StudentbladetRenderer,))
def studentbladetDump(request):
    recipients = Member.objects.exclude(dead=True).filter(allow_studentbladet=True)
    recipients = [m for m in recipients if m.isValidMember()]

    content = [{
        'name': recipient._get_full_name(),
        'street_address': recipient.street_address,
        'postal_code': recipient.postal_code,
        'city': recipient.city,
        'country': recipient.country
        } for recipient in recipients]

    dumpname = 'filename="studentbladetdump_{}.csv"'.format(datetime.today().date())
    return Response(
            content,
            status=200,
            headers={'Content-Disposition': 'attachment; {}'.format(dumpname)}
        )
