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
                self.fields["participant"].queryset = models.Team.objects.filter(
                    pk=user_participation.team.pk
                )
