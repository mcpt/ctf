from django.db.models import F
from gameserver.models.cache import ContestScore
from gameserver.models.contest import ContestProblem
from ninja import NinjaAPI, Schema
from typing import List

def unicode_safe(string):
    return string.encode("unicode_escape").decode()
        
api = NinjaAPI()

class CTFSchema(Schema):
    pos: int
    team: str
    score: int
    
class CTFTimeSchema(Schema):
    standings: List[CTFSchema]
    tasks: List[str]
    
@api.get("/ctftime", response=CTFTimeSchema)
def add(request, contest_id: int):
    standings = ContestScore.ranks(contest=contest_id).annotate(pos=F("rank"), score=F("points"), team=F("participation__team__name"))
        # .only("pos", "team", "score")
    task_names = ContestProblem.objects.filter(contest_id=contest_id).prefetch_related("problem__name").values_list("problem__name")
    
    return {"standings": standings, "tasks": task_names}