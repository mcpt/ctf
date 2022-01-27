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


class TeamUpdateForm(ModelForm):
    class Meta:
        model = models.Team
        fields = [
            "name",
            "description",
            "members",
            "access_code",
        ]
        widgets = {"members": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        team = kwargs.pop("team", None)
        super(TeamUpdateForm, self).__init__(*args, **kwargs)
        self.fields["members"].queryset = team.members.all()
        self.initial["members"] = [i.pk for i in team.members.all()]


class GroupJoinForm(forms.Form):
    access_code = forms.CharField(
        max_length=36,
        strip=True,
        widget=forms.TextInput(attrs={"placeholder": "Access Code"}),
        label="Enter the access code to join",
    )

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop("group", None)
        super(GroupJoinForm, self).__init__(*args, **kwargs)

    def clean_access_code(self):
        if self.cleaned_data["access_code"] != self.group.access_code:
            raise ValidationError("Incorrect Access Code", code="forbidden")
