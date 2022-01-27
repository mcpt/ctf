from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm

from . import models
from .models import choices

User = get_user_model()


class MCTFSignupForm(SignupForm):
    timezone = forms.ChoiceField(choices=choices.timezone_choices, initial=settings.DEFAULT_TIMEZONE)
    full_name = forms.CharField(max_length=80)
    school_name = forms.CharField(max_length=80, required=False)
    school_contact = forms.EmailField(required=False)
    field_order = [
        "full_name",
        "email",
        "username",
        "password1",
        "password2",
        "timezone",
        "school_name",
        "school_contact",
    ]

    def save(self, request):
        user = super(MCTFSignupForm, self).save(request)
        user.timezone = self.cleaned_data["timezone"]
        user.full_name = self.cleaned_data["full_name"]
        user.school_name = self.cleaned_data["school_name"]
        user.school_contact = self.cleaned_data["school_contact"]
        user.save()
        return user


class ProfileUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = [
            "description",
            "timezone",
            # "payment_pointer",
            "organizations",
            "school_name",
            "school_contact"
        ]
        widgets = {"organizations": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        if not user.has_perm("gameserver.edit_all_organization"):
            self.fields["organizations"].queryset = models.Organization.objects.filter(
                Q(is_private=False) | Q(admins=user) | Q(pk__in=user.organizations.all())
            ).distinct()
        self.initial["organizations"] = [i.pk for i in user.organizations.all()]
        self.initial["school_name"] = user.school_name
        self.initial["school_contact"] = user.school_contact
        self.fields["description"].label = "Profile description"
        self.fields["description"].widget.attrs['placeholder'] = "Description..."
