from members.models import *
from members.utils import *
from registration.models import Applicant
from django.forms import ModelForm, DateField, CharField
from django.forms.widgets import CheckboxInput, DateInput, TextInput, PasswordInput
from ajax_select.fields import AutoCompleteSelectMultipleField
from django.contrib.auth.forms import AuthenticationForm
from django import forms


class BSModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(BSModelForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MemberForm(ModelForm):
    class Meta:
        model = Member
        fields = '__all__'
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'cols': 15}),
        }

    birth_date = DateField(widget=DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "mform_%s"
        super(MemberForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            if type(field.widget) is CheckboxInput:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class GroupTypeForm(BSModelForm):
    class Meta:
        model = GroupType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "gtform_%s"
        super(GroupTypeForm, self).__init__(*args, **kwargs)


class FunctionaryTypeForm(BSModelForm):
    class Meta:
        model = FunctionaryType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "ftform_%s"
        super(FunctionaryTypeForm, self).__init__(*args, **kwargs)


class FunctionaryForm(BSModelForm):
    class Meta:
        model = Functionary
        fields = '__all__'

    member = AutoCompleteSelectMultipleField('member', required=True, help_text=None)
    begin_date = DateField(widget=DateInput(attrs={'type': 'date'}))
    end_date = DateField(widget=DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "fform_%s"
        kwargs["initial"] = {
            "begin_date": getFirstDayOfCurrentYear(),
            "end_date": getLastDayOfCurrentYear(),
            **(kwargs["initial"] if "initial" in kwargs else {}),
        }
        super(FunctionaryForm, self).__init__(*args, **kwargs)


class DecorationForm(BSModelForm):
    class Meta:
        model = Decoration
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "dform_%s"
        super(DecorationForm, self).__init__(*args, **kwargs)


class DecorationOwnershipForm(BSModelForm):
    class Meta:
        model = DecorationOwnership
        fields = '__all__'

    acquired = DateField(widget=DateInput(attrs={'type': 'date'}))
    member = AutoCompleteSelectMultipleField('member', required=True, help_text=None)

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "doform_%s"
        kwargs["initial"] = {
            "acquired": getCurrentDate(),
            **(kwargs["initial"] if "initial" in kwargs else {}),
        }
        super(DecorationOwnershipForm, self).__init__(*args, **kwargs)


class GroupForm(BSModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    begin_date = DateField(widget=DateInput(attrs={'type': 'date'}))
    end_date = DateField(widget=DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "gform_%s"
        kwargs["initial"] = {
            "begin_date": getFirstDayOfCurrentYear(),
            "end_date": getLastDayOfCurrentYear(),
            **(kwargs["initial"] if "initial" in kwargs else {}),
        }
        super(GroupForm, self).__init__(*args, **kwargs)


class GroupMembershipForm(BSModelForm):
    class Meta:
        model = GroupMembership
        fields = '__all__'

    member = AutoCompleteSelectMultipleField('member', required=True, help_text=None)

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "gmform_%s"
        super(GroupMembershipForm, self).__init__(*args, **kwargs)


class MemberTypeForm(BSModelForm):
    class Meta:
        model = MemberType
        fields = '__all__'

    begin_date = DateField(widget=DateInput(attrs={'type': 'date'}))
    end_date = DateField(required=False, widget=DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "mtform_%s"
        kwargs["initial"] = {
            "begin_date": getCurrentDate(),
            **(kwargs["initial"] if "initial" in kwargs else {}),
        }
        super(MemberTypeForm, self).__init__(*args, **kwargs)


class BSAuthForm(AuthenticationForm):
    username = CharField(widget=TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Användarnamn', 'autofocus': 'on'
    }))
    password = CharField(widget=PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Lösenord'}))


class ApplicantAdditionForm(BSModelForm):
    class Meta:
        model = Applicant
        fields = '__all__'

    membership_date = DateField(widget=DateInput(attrs={'type': 'date'}))
    phux_date = DateField(widget=DateInput(attrs={'type': 'date'}), required=False)

    def __init__(self, *args, **kwargs):
        # Make sure automatic dom element ids are different from other forms'
        if "auto_id" not in kwargs:
            kwargs["auto_id"] = "aaform_%s"
        super(ApplicantAdditionForm, self).__init__(*args, **kwargs)


class MultipleApplicantAdditionForm(ApplicantAdditionForm):
    applicant = AutoCompleteSelectMultipleField('applicant', required=True, help_text=None)
