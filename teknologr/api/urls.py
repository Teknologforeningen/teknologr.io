from django.conf.urls import url, include
from rest_framework.routers import APIRootView, DefaultRouter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from api.views import *

class TeknologrRootView(APIRootView):
    permission_classes = (IsAuthenticated, )
    name = 'Katalogen root API'
    description = ''
    router_list_name = None
    router_registry = None

    @property
    def api_root_dict(self):
        '''
        Overriding the parent attribute to be able to filter views based on permissions.

        This is accessed by the get() method and is by default provided by the router instead.
        '''
        d = {}
        is_staff = self.request.user.is_staff
        for prefix, viewset, basename in self.router_registry:
            # Include the route unless it is staff only
            if not is_staff and IsAdminUser in viewset.permission_classes:
                continue
            d[prefix] = self.router_list_name.format(basename=basename)

        # Also add the other named API endpoints to the list (mainly the dumps)
        # XXX: Is there a way to check the permissions agains the user for these too?
        if is_staff:
            for url in urlpatterns:
                if hasattr(url, 'name') and url.name:
                    d[url.name] = url.name

        return d

class TeknologrRouter(DefaultRouter):
    APIRootView = TeknologrRootView

    def get_api_root_view(self, api_urls=None):
        return self.APIRootView.as_view(router_list_name=self.routes[0].name, router_registry=self.registry)


# Routers provide an easy way of automatically determining the URL conf.
# NOTE: Use for example {% url 'api:member-list' %} to access these urls
router = TeknologrRouter()
router.register(r'members', MemberViewSet)
router.register(r'grouptypes', GroupTypeViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'groupmemberships', GroupMembershipViewSet)
router.register(r'functionarytypes', FunctionaryTypeViewSet)
router.register(r'functionaries', FunctionaryViewSet)
router.register(r'decorations', DecorationViewSet)
router.register(r'decorationownerships', DecorationOwnershipViewSet)
router.register(r'membertypes', MemberTypeViewSet)
router.register(r'applicants', ApplicantViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^multi-groupmemberships/$', multi_group_memberships_save, name='multi_groupmemberships'),
    url(r'^multi-functionaries/$', multi_functionaries_save, name='multi_functionaries'),
    url(r'^multi-decorationownerships/$', multi_decoration_ownerships_save, name='multi_decorationownerships'),
    url(r'^multi-applicantsubmissions/$', multi_applicant_submissions),

    url(r'^ldap/users/$', get_ldap_user_list),
    url(r'^ldap/users/(.+)/$', get_ldap_user_details, name='ldap_user'),
    url(r'^ldap/groups/$', get_ldap_group_list),
    url(r'^ldap/groups/(.+)/$', get_ldap_group_details, name='ldap_group'),
    url(r'^accounts/ldap/(\d+)/$', LDAPAccountView.as_view(), name='ldap_account'),
    url(r'^accounts/ldap/change_pw/(\d+)/$', change_ldap_password, name='ldap_change_pw'),
    url(r'^accounts/bill/(\d+)/$', BILLAccountView.as_view(), name='bill'),
    url(r'^applicants/make-member/(\d+)/$', ApplicantMembershipView.as_view(), name='make_member'),
    url(r'^dump-htk/(?:(\d+)/)?$', dump_htk, name='dump_htk'),
    url(r'^dump-modulen/$', dump_modulen, name='dump_modulen'),
    url(r'^dump-active/$', dump_active, name='dump_active'),
    url(r'^dump-arsk/$', dump_arsk, name='dump_arsk'),
    url(r'^dump-regemails/$', dump_reg_emails, name='dump_reg_emails'),
    url(r'^dump-studentbladet/$', dump_studentbladet, name='dump_studentbladet'),
    # Used by BILL (?), allowing any username even if it includes "forbidden" characters
    url(r'^memberTypesForMember/(?P<mode>username|studynumber)/(?P<query>.+)/$', member_types_for_member),
    # Used by BILL and Generikey
    url(r'^membersByMemberType/([A-Z]{2})/(?:(\w+)/?)?$', members_by_member_type),
]
