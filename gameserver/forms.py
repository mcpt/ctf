from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django import forms
from django.forms import ModelForm
from django.db.models import Q

from . import models

from allauth.account.forms import SignupForm
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3

User = get_user_model()


class PCTFSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3, label="")
    field_order = ["email", "username", "password1", "password2", "captcha"]


class ProfileUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = [
            "description",
            "timezone",
            "payment_pointer",
            "organizations",
        ]
        widgets = {"organizations": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        if not user.has_perm("gameserver.edit_all_organization"):
            self.fields["organizations"].queryset = models.Organization.objects.filter(
                Q(is_private=False)
                | Q(admins=user)
                | Q(pk__in=user.organizations.all())
            ).distinct()
        self.initial["organizations"] = [i.pk for i in user.organizations.all()]


class OrganizationJoinForm(forms.Form):
    access_code = forms.CharField(max_length=36, strip=True)

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop("organization", None)
        super(OrganizationJoinForm, self).__init__(*args, **kwargs)

    def clean_access_code(self):
        if self.cleaned_data["access_code"] != self.organization.access_code:
            raise ValidationError("Incorrect Access Code", code="forbidden")
