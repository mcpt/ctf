import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Sum, Max
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from . import abstract

# Create your models here.


class ContestTag(abstract.Category):
    pass


class Contest(models.Model):
    organizers = models.ManyToManyField(
        "User", related_name="contests_organized", blank=True
    )
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

    problems = models.ManyToManyField(
        "Problem", related_name="contests_featured_in", blank=True
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("contest_detail", args=[self.slug])

    def is_started(self):
        return self.start_time <= timezone.now()

    def is_finished(self):
        return self.end_time < timezone.now()

    def is_ongoing(self):
        return self.is_started() and not self.is_finished()

    def duration(self):
        return self.end_time - self.start_time

    def ranks(self):
        return self.participations.annotate(
            cum_points=Coalesce(Sum("solves__solve__problem__points"), 0),
            most_recent_solve_time=Coalesce(Max("solves__solve__created"), self.start_time),
        ).order_by("-cum_points", "most_recent_solve_time")


class ContestParticipation(models.Model):
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="participations"
    )
    is_disqualified = models.BooleanField(default=False)

    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        related_name="contest_participations",
        null=True,
        blank=True,
    )

    participants = models.ManyToManyField(
        "User", related_name="contest_participations", blank=True
    )

    def participant(self):
        if self.team is None:
            return self.participants.first()
        else:
            return self.team

    def points(self):
        points = self.solves.aggregate(points=Coalesce(Sum("solve__problem__points"), 0))["points"]
        return points

    def num_flags_captured(self):
        return self.solves.count()

    def last_solve(self):
        solves = self.solves.order_by('-solve__created')
        if solves.count() >= 1:
            return solves[0]
        else:
            return None

    def last_solve_time(self):
        last_solve = self.last_solve()
        if last_solve is not None:
            return last_solve.solve.created
        else:
            return self.contest.start_time

    def time_taken(self):
        solve_time = self.last_solve_time()
        return solve_time - self.contest.start_time

    def rank(self):
        points = self.points()
        last_solve_time = self.last_solve_time()
        contest_ranks = self.contest.ranks()
        return (
            contest_ranks
            .filter(Q(cum_points__gt=points) | Q(most_recent_solve_time__lte=last_solve_time) & Q(cum_points=points))
            .count()
        )

    def get_absolute_url(self):
        return reverse("contest_participation_detail", args=[self.pk])

    def has_solved(self, problem):
        solves = self.solves.filter(solve__problem=problem)
        return solves.count() > 0

    def __str__(self):
        return f"{self.participant().__str__()}'s Participation in {self.contest.name}"


class ContestSolve(models.Model):
    participation = models.ForeignKey(
        ContestParticipation, on_delete=models.CASCADE, related_name="solves"
    )
    solve = models.OneToOneField(
        "Solve", on_delete=models.CASCADE, related_name="contest_solve"
    )
