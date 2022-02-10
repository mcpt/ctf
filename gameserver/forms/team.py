from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm

from .. import models
from ..models import choices

User = get_user_model()


class TeamUpdateForm(ModelForm):
    class Meta:
        model = models.Team
        fields = [
            "name",
            "description",
            "members",
            "organizations",
            "access_code",
        ]
        widgets = {
            "members": forms.CheckboxSelectMultiple(),
            "organizations": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(TeamUpdateForm, self).__init__(*args, **kwargs)

        self.fields["members"].queryset = self.instance.members.all()
        self.initial["members"] = [i.pk for i in self.instance.members.all()]

        self.fields["organizations"].queryset = self.instance.owner.organizations.all()
        self.initial["organizations"] = [i.pk for i in self.instance.organizations.all()]
