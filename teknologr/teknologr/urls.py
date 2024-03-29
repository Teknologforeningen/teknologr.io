"""teknologr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from members.forms import BSAuthForm
from ajax_select import urls as ajax_select_urls

urlpatterns = [
    url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html', authentication_form=BSAuthForm)),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    url(r'^', include(('katalogen.urls', 'katalogen'), namespace='katalogen')),
    url(r'^admin/', include(('members.urls', 'admin'), namespace='admin')),
    url(r'^api/', include(('api.urls', 'api'), namespace='api')),
    url(r'^registration/', include(('registration.urls', 'registration'), namespace='registration')),
    url(r'^ajax_select/', include(ajax_select_urls)),
]
