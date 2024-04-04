from django.http import HttpRequest
from django.db.models import F
from gameserver.models.cache import ContestScore
from django.http import JsonResponse


def unicode_safe(string):
    return string.encode("unicode_escape").decode()


def CtfTime(request: HttpRequest, contest_id: int):
    standings = (
        ContestScore.ranks()
        .annotate(pos=F("rank"), score=F("points"), team="participation__team__name")
        .only("pos", "team", "score")
    )
    return JsonResponse(standings.values_list())
