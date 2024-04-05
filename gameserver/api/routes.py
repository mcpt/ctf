from django.db.models import F, OuterRef, Subquery, Case, When, Q
from django.shortcuts import get_object_or_404

from gameserver.models.cache import ContestScore
from gameserver.models.contest import ContestProblem, ContestSubmission, Contest
from ninja import NinjaAPI, Schema
from typing import List, Any


def unicode_safe(string):
    return string.encode("unicode_escape").decode()


api = NinjaAPI()


class CTFSchema(Schema):
    pos: int
    team: Any = None
    score: int
    lastAccept: Any = None

    @staticmethod
    def resolve_lastAccept(obj) -> int:
        """Turns a datetime object into a timestamp."""
        if obj["lastAccept"] is None:
            return 0
        return int(obj["lastAccept"].timestamp())

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
            team=F("participation__team__name"),
            # team=Coalesce(F("participation__team__name"), F("participation__participants__username")),
            # Using Coalesce and indexing
            # team=Case(
            #     When(F("participation__team__isnull")==True, then=Q(("participation__participants")[0]["username"])),
            #     default=F("team_name"),
            #     output_field=TextField(),
            # ),
            lastAccept=Subquery(last_sub_time),
        )
        .values("pos", "score", "team", "lastAccept")
    )
    task_names = (
        ContestProblem.objects.filter(contest_id=contest_id)
        .prefetch_related("problem__name")
        .values_list("problem__name", flat=True)
    )

    return {"standings": standings, "tasks": task_names}
