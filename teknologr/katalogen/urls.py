from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^search/$', views.search, name='search'),
    url(r'^([A-ZÅÄÖ])/$', views.startswith, name='startswith'),
    url(r'^members/$', views.home),
    url(r'^members/(\d+)/$', views.profile, name='profile'),
    url(r'^members/(\d+)/info$', views.profile_info, name='profile_info'),
    url(r'^members/(\d+)/edit$', views.profile_edit, name='profile_edit'),
    url(r'^person/(\d+)/$', views.profile),
    url(r'^profile/$', views.myprofile, name='myprofile'),
    url(r'^decorations/$', views.decorations, name='decorations'),
    url(r'^decorations/(\d+)/$', views.decoration, name='decoration'),
    url(r'^functionaries/$', views.functionary_types, name='functionary_types'),
    url(r'^functionaries/(\d+)/$', views.functionary_type, name='functionary_type'),
    url(r'^groups/$', views.group_types, name='group_types'),
    url(r'^groups/(\d+)/$', views.groups, name='groups'),
    url(r'^groupmemberships/(\d+)/$', views.group_memberships, name='group_memberships'),
    url(r'^years/$', views.years, name='years'),
    url(r'^years/(\d+)/$', views.year, name='year'),
]
