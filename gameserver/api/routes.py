from django.db.models import F
from gameserver.models.cache import ContestScore
from gameserver.models.contest import ContestParticipation
from ninja import NinjaAPI, Schema
from typing import List

def unicode_safe(string):
    return string.encode("unicode_escape").decode()
        
api = NinjaAPI()

class CTFSchema(Schema):
    pos: int
    team: str
    score: int
    
@api.get("/ctftime", response=List[CTFSchema])
def add(request, contest_id: int):
    return  (
        ContestScore.ranks(contest=contest_id)
        .annotate(pos=F("rank"), score=F("points"), team=F("participation__team__name"))
        # .only("pos", "team", "score")
    )