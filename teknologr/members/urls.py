from django.conf.urls import patterns, url, include
from django.views.generic import RedirectView
from . import views
from ajax_select import urls as ajax_select_urls


urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/admin/members/')),
    url(r'^(members|groups|functionaries|decorations)/$', views.empty),
    url(r'^members/(\d+)/$', views.member),
    url(r'^membertype/(\d+)/form/$', views.membertype_form),
    url(r'^groups/(\d+)/$', views.group),
    url(r'^groups/(\d+)/(\d+)/$', views.group),
    url(r'^functionaries/(\d+)/$', views.functionary),
    url(r'^decorations/(\d+)/$', views.decoration),
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'^groups/(?P<group_id>\d+)/(?P<subgroup_id>\d+)/download', views.download_group_members)
]
