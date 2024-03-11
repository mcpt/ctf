from django.db import models, transaction
from django.db.models.functions import Coalesce
from django.db.models import Count, F, Sum
from .profile import User


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contest import ContestParticipation, Contest
        
    
class UserScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, unique=True)
    points = models.PositiveIntegerField(help_text="The amount of points.", default=0)
    flag_count = models.PositiveIntegerField(help_text="The amount of flags the user/team has.", default=0)
    
    def __str__(self) -> str:
        return f"{self.user_id}'s score"
    
    @classmethod
    def update_or_create(cls, change_in_score: int, user: User, update_flags: bool = True):
        assert change_in_score > 0
        queryset = cls.objects.filter(user=user)
        
        if not queryset.exists(): # no user found matching that
            cls.objects.create(user=user, flag_count=int(update_flags), points=change_in_score) 
            return cls.update_or_create(change_in_score=change_in_score, user=user, update_flags=update_flags)
        
        if update_flags:
            queryset.update(points=F('points') + change_in_score)   
        else:
            queryset.update(points=F('points') + change_in_score, flag_count=F('flag_count') + 1)   
    
    @classmethod
    def invalidate(cls, user: User):
        try:
            cls.objects.get(user=user).delete()
        except cls.DoesNotExist:
            pass # user was not found.
            
    
    @classmethod
    def get(cls, user: User) -> None | "UserScore":        
        obj = cls.objects.filter(user=user)
        if obj is None:
            return None
        return obj.first()
    
    @classmethod
    def initalize_data(cls):
        cls.objects.all().delete() # clear inital objs
        users = User.objects.all()
        scores_to_create = []
        for user in users:
            queryset = user._get_unique_correct_submissions()
            queryset = queryset.aggregate(
                points=Coalesce(Sum("problem__points"), 0),
                flags=Count("problem"),
            )
            scores_to_create.append(
                UserScore(
                    user=user,
                    flag_count=queryset['flags'],
                    points=queryset['points']
                )
            )
        # Use bulk_create to create all objects in a single query
        cls.objects.bulk_create(scores_to_create)
        
        


    
class ContestScore(models.Model):
    participation=models.ForeignKey("ContestParticipation", on_delete=models.CASCADE, db_index=True, unique=True)
    points = models.PositiveIntegerField(help_text="The amount of points.", default=0)
    flag_count = models.PositiveIntegerField(help_text="The amount of flags the user/team has.", default=0)
    
    def __str__(self) -> str:
        return f'Score for {self.participation} on {self.participation.contest.name}'


    @classmethod
    def update_or_create(cls, change_in_score: int, participant: "ContestParticipation", update_flags: bool = True):
        assert change_in_score > 0
        queryset = cls.objects.filter(participation=participant)
        
        if not queryset.exists(): # no user/team found matching that
            cls.objects.create(participation=participant, flag_count=int(update_flags), points=change_in_score) 
            return cls.update_or_create(change_in_score=change_in_score, participant=participant, update_flags=update_flags)
        
        with transaction.atomic():
            queryset.select_for_update() # prevent race conditions with other team members

            if update_flags:
                queryset.update(points=F('points') + change_in_score)   
            else:
                queryset.update(points=F('points') + change_in_score, flag_count=F('flag_count') + 1)   
    
    @classmethod
    def invalidate(cls, participant: ContestParticipation):
        try:
            cls.objects.get(participant=participant).delete()
        except cls.DoesNotExist:
            pass # participant was not found.
            
    
    @classmethod
    def get(cls, participant: ContestParticipation) -> None | "ContestScore":        
        obj = cls.objects.filter(participant=participant)
        if obj is None:
            return None
        return obj.first()
    
    @classmethod
    def initalize_data(cls, contest: "Contest"):
        cls.objects.all().delete() # clear inital objs
        participants = contest.participations.all()
        scores_to_create = []
        for participant in participants:
            queryset = participant._get_unique_correct_submissions()
            queryset = queryset.aggregate(
                points=Coalesce(Sum("problem__points"), 0),
                flags=Count("problem"),
            )
            scores_to_create.append(
                ContestScore(
                    participation=participant,
                    flag_count=queryset['flags'],
                    points=queryset['points']
                )
            )
        # Use bulk_create to create all objects in a single query
        cls.objects.bulk_create(scores_to_create)
        
        

