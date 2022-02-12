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

        if (
            self.user.current_contest is not None
            and self.user.current_contest.contest == self.contest
        ):
            # Upgrade to a team
            self.fields["participant"].required = True
            if self.user.current_contest.team is None:
                # Not participating as a team currently
                self.fields["participant"].queryset = self.user.teams
            return

        # Search for an existing participation
        user_participation = self.user.participation_for_contest(self.contest)

        if user_participation is not None and user_participation.team is not None:
            # Already participating as a team
            self.fields["participant"].required = True
            self.fields["participant"].initial = user_participation.team
            self.fields["participant"].queryset = models.Team.objects.filter(
                pk=user_participation.team.pk
            )
            return

        # Already participating as an individual or not participating at all
        self.fields["participant"].empty_label = f"Myself ({self.user.username})"

        if user_participation is None and self.contest.teams_allowed:
            # No participation yet, and teams are allowed
            self.fields["participant"].queryset = self.user.teams

    def clean_participant(self):
        team = self.cleaned_data["participant"]

        if team is not None:
            team_participation = team.participation_for_contest(self.contest)
            if team_participation is not None:
                team_participants = team_participation.participants.all()
                if (
                    self.contest.max_team_size is not None
                    and team_participants.count() >= self.contest.max_team_size
                ):
                    raise ValidationError(
                        "This team is full for this contest. Please choose another team or join as an individual."
                    )

        return team
