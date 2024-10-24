
from members.models import Member
from members.forms import BSModelForm
from members.validators import CommonValidators
from ldap import LDAPError

class EditProfileForm(BSModelForm, CommonValidators):
    class Meta:
        model = Member
        fields = ['preferred_name', 'phone', 'email', 'street_address', 'postal_code', 'city', 'country', 'graduated', 'graduated_year', 'subscribed_to_modulen', 'allow_studentbladet', 'allow_publish_info']

    def clean(self):
        BSModelForm.clean(self)
        CommonValidators.clean(self)
