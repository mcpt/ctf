from django.db.models import F, OuterRef, Subquery
from gameserver.models.cache import ContestScore
from gameserver.models.contest import ContestProblem, ContestSubmission
from ninja import NinjaAPI, Schema
from typing import List, Any

def unicode_safe(string):
    return string.encode("unicode_escape").decode()
        
api = NinjaAPI()

class CTFSchema(Schema):
    pos: int
    team: str
    score: int
    lastAccept: Any
    
class CTFTimeSchema(Schema):
    standings: List[CTFSchema]
    tasks: List[str]
    
@api.get("/ctftime", response=CTFTimeSchema)
def add(request, contest_id: int):
    last_sub_time =  ContestSubmission.objects.filter(
                participation=OuterRef("pk"), submission__is_correct=True
            ).values("submission__date_created")
    standings = ContestScore.ranks(contest=contest_id).annotate(pos=F("rank"), score=F("points"), team=F("participation__team__name"), lastAccept=Subquery(last_sub_time))
        # .only("pos", "team", "score")
    task_names = ContestProblem.objects.filter(contest_id=contest_id).prefetch_related("problem__name").values_list("problem__name")
    
    return {"standings": standings, "tasks": task_names}