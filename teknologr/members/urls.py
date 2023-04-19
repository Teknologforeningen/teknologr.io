from django.conf.urls import url, include
from django.views.generic import RedirectView
from . import views


urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/admin/members/'), name='home'),
    url(r'^(members|grouptypes|functionarytypes|decorations|applicants)/$', views.empty, name='empty'),
    url(r'^members/(\d+)/$', views.member, name='member'),
    url(r'^membertypes/(\d+)/form/$', views.membertype_form),
    url(r'^grouptypes/(\d+)/$', views.group_type, name='group_type'),
    url(r'^grouptypes/(\d+)/(\d+)/$', views.group_type, name='group'),
    url(r'^functionarytypes/(\d+)/$', views.functionary_type, name='functionary_type'),
    url(r'^decorations/(\d+)/$', views.decoration, name='decoration'),
    url(r'^applicants/(\d+)/$', views.applicant, name='applicant'),
]
