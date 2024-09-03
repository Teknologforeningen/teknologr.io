from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.db.models import F
from django.urls import reverse
from members.views import set_side_context
from members.models import *

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def base(request):
    context = {}
    set_side_context(context)

    context['tests'] = [{
        'title': 'Inget mellanslag i Member.preferred_name',
        'id': 'space_in_preferred_name',
    },{
        'title': 'Member.preferred_name måste finnas bland Member.given_names',
        'id': 'preferred_name_in_given_names',
    }]

    return render(request, 'validity.html', context)

@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def test(_, id):
    d = { 'id': id }

    if id == "space_in_preferred_name":
        members = list(Member.objects.filter(preferred_name__icontains=" "))
        Member.order_by(members, 'name')
        d["results"] = [{ 'text': m.get_full_name_HTML(), 'href': reverse('admin:member', args=[m.id]) } for m in members]

    elif id == "preferred_name_in_given_names":
        members = list(Member.objects.filter(given_names__contains=F('preferred_name')))
        Member.order_by(members, 'name')
        d["results"] = [{ 'text': m.get_full_name_HTML(), 'href': reverse('admin:member', args=[m.id]) } for m in members]

    return JsonResponse(d)
