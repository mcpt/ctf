from django.db import models
import uuid
from django.urls import reverse
from . import abstract
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum

# Create your models here.


class ContestTag(abstract.Category):
    pass


class Contest(models.Model):
    organizers = models.ManyToManyField('User', related_name="contests_organized", blank=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    summary = models.CharField(max_length=150)
    created = models.DateTimeField(auto_now_add=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    tags = models.ManyToManyField(ContestTag, blank=True)

    is_private = models.BooleanField(default=True)

    teams_allowed = models.BooleanField(default=True)

    problems = models.ManyToManyField('Problem', related_name="contests_featured_in", blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('contest_detail', args=[self.slug])

    def is_started(self):
        return self.start_time <= timezone.now()

    def is_finished(self):
        return self.end_time < timezone.now()

    def is_ongoing(self):
        return self.is_started() and not self.is_finished()

class ContestParticipation(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participations')
    is_disqualified = models.BooleanField(default=False)

    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='contest_participations', null=True, blank=True)

    participants = models.ManyToManyField('User', related_name="contest_participations", blank=True)

    def participant(self):
        if self.team is None:
            return self.participants.first()
        else:
            return self.team

    def points(self):
        points = self.solves.aggregate(points=Sum('solve__problem__points'))['points']
        if points is None:
            return 0
        else:
            return points

    def num_flags_captured(self):
        return self.solves.count()

    def get_absolute_url(self):
        return reverse('contest_participation_detail', args=[self.pk])

    def __str__(self):
        return f"{self.participant().__str__()}'s Participation in {self.contest.name}"

class ContestSolve(models.Model):
    participation = models.ForeignKey(ContestParticipation, on_delete=models.CASCADE, related_name='solves')
    solve = models.OneToOneField('Solve', on_delete=models.CASCADE, related_name='contest_solve')
