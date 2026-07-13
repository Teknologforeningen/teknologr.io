from ajax_select import register, LookupChannel
from members.models import Member
from registration.models import Applicant
from django.db.models import Q


@register('member')
class MemberLookup(LookupChannel):
    model = Member

    def get_query(self, q, request):
        if q == '__ALL__':
            return Member.objects.order_by('-modified')[:50]

        members = Member.objects.search_by_name(q.split(), True)
        Member.order_by(members, 'name')
        return members[:50]

    def get_result(self, obj):
        """ result is the simple text that is the completion of what the person typed """
        return obj.full_name

    def format_match(self, obj):
        """ (HTML) formatted item for display in the dropdown """
        return obj.get_full_name_HTML()

    def format_item_display(self, obj):
        """ (HTML) formatted item for displaying item in the selected deck area """
        return obj.full_name


@register('applicant')
class ApplicantLookup(LookupChannel):
    model = Applicant

    def get_query(self, q, request):
        applicants = Applicant.objects.search_by_name(q.split())
        Applicant.order_by(applicants, 'name')
        return applicants[:50]

    def get_result(self, obj):
        return obj.full_name

    def format_match(self, obj):
        return obj.get_full_name_HTML()

    def format_item_display(self, obj):
        return obj.full_name
