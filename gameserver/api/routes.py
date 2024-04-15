import datetime
from typing import Any, List

from django.db.models import F, OuterRef, Max, Subquery, Case, When, Value, BooleanField, TextField
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema

from gameserver.models.cache import ContestScore
from gameserver.models.profile import User
from gameserver.models.contest import Contest, ContestProblem, ContestSubmission, ContestParticipation


def unicode_safe(string):
    return string.encode("unicode_escape").decode()


api = NinjaAPI()


class ContestOutSchema(Schema):
    name: str
    slug: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    max_team_size: int | None
    description: str
    summary: str


class CTFSchema(Schema):
    pos: int
    team: Any = None
    score: int
    lastAccept: Any = None

    @staticmethod
    def resolve_lastAccept(obj: dict) -> int:
        """Turns a datetime object into a timestamp."""
        print(obj, ' - DEBUG PRINT')
        if obj['lastAccept'] is None:
            return 0
        return int(obj['lastAccept'].timestamp())

    @staticmethod
    def resolve_team(obj):
        return unicode_safe(obj["team"])


class CTFTimeSchema(Schema):
    standings: List[CTFSchema]
    tasks: List[str]


@api.get("/ctftime/{contest_name}", response=CTFTimeSchema)
def ctftime_standings(request, contest_name: str):
    contest_id = get_object_or_404(Contest, name__iexact=contest_name).id
    """Get the standings for a contest in CTFTime format."""
    last_sub_time = (
        ContestSubmission.objects.filter(
            participation_id=OuterRef("participation_id"), submission__is_correct=True
        )
        .prefetch_related("submission")
        .order_by("-submission__date_created")
        .values("submission__date_created")
    )

    standings = (
        ContestScore.ranks(contest=contest_id)
        .annotate(
            pos=F("rank"),
            score=F("points"),
            is_solo=Case(
                When(participation__team_id=None, then=Value(False)),
                default=Value(True),
                output_field=BooleanField(),
            ),
            team=Case(
                When(participation__team_id=None, then=Subquery(     # If the team is None, use the username of the participant ( solo player )
                    User.objects.filter(contest_participations=OuterRef("participation_id")).values(
                        "username")[:1]
                ),),
                default=F("participation__team__name"),
                output_field=TextField(),
            ),
            lastAccept=Max("participation__submission__submission__date_created"),
        )
        .filter(score__gt=0)
        .values("pos", "score", "team", "lastAccept")
    )
    task_names = (
        ContestProblem.objects.filter(contest_id=contest_id)
        .prefetch_related("problem__name")
        .values_list("problem__name", flat=True)
    )

    return {"standings": standings, "tasks": task_names}


@api.get("/contests", response=List[ContestOutSchema])
def contests(request):
    return Contest.objects.filter(is_public=True).values(
        "name", "slug", "start_time", "end_time", "max_team_size", "description", "summary"
    )
