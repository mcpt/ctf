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


class FlagSubmissionForm(forms.Form):
    flag = forms.CharField(
        max_length=256,
        strip=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "mCTF{}"}),
    )

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem", None)
        super(FlagSubmissionForm, self).__init__(*args, **kwargs)

    def clean_flag(self):
        if self.cleaned_data["flag"] != self.problem.flag:
            raise ValidationError("Incorrect Flag", code="incorrect")


class ContestJoinForm(forms.Form):
    participant = forms.ModelChoiceField(
        queryset=models.Team.objects.none(),
        label="Participate as",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.contest = kwargs.pop("contest", None)
        super(ContestJoinForm, self).__init__(*args, **kwargs)
        if not self.user.is_authenticated:
            return
        self.fields["participant"].empty_label = f"Myself ({self.user.username})"
        if self.contest.teams_allowed:
            self.fields["participant"].queryset = self.user.eligible_teams(self.contest)

        user_participations = self.user.participations_for_contest(self.contest)
        if user_participations.count() > 0:
            user_participation = user_participations.first()
            if user_participation.team is not None:
                self.fields["participant"].required = True
                self.fields["participant"].empty_label = None
                self.fields["participant"].queryset = models.Team.objects.filter(pk=user_participation.team.pk)
