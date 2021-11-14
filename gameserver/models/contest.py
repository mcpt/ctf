import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Sum, Max, Min, Count
from django.db.models import OuterRef, Subquery
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
    date_created = models.DateTimeField(auto_now_add=True)

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
        submissions_with_points = ContestSubmission.objects.filter(participation=OuterRef("pk")).order_by().values("submission__problem").distinct().annotate(sub_pk=Min("pk")).values('sub_pk')
        return self.participations.annotate(
                points=Coalesce(Sum("submissions__submission__problem__points", filter=Q(submissions__in=Subquery(submissions_with_points))), 0),
                flags=Coalesce(Count("submissions__pk", filter=Q(submissions__in=Subquery(submissions_with_points))), 0),
                most_recent_solve_time=Coalesce(Max("submissions__submission__date_created", filter=Q(submissions__in=Subquery(submissions_with_points))), self.start_time),
            ).order_by("-points", "most_recent_solve_time", "flags")


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

    def _get_unique_correct_submissions(self):
        # Switch to ContestProblem -> Problem Later
        return self.submissions.filter(submission__is_correct=True).values("submission__problem", "submission__problem__points").distinct()

    def points(self):
        points = self._get_unique_correct_submissions().aggregate(points=Coalesce(Sum("submission__problem__points"), 0))["points"]
        return points

    def num_flags_captured(self):
        return self._get_unique_correct_submissions().count()

    def last_solve(self):
        submissions = self.submissions.filter(submission__is_correct=True).order_by('-submission__date_created')
        if submissions.count() >= 1:
            return submissions[0]
        else:
            return None

    def last_solve_time(self):
        last_solve = self.last_solve()
        if last_solve is not None:
            return last_solve.submission.date_created
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
            .filter(Q(points__gt=points) | Q(most_recent_solve_time__lte=last_solve_time) & Q(points=points))
            .count()
        )

    def get_absolute_url(self):
        return reverse("contest_participation_detail", args=[self.pk])

    def has_solved(self, problem):
        solves = self.submissions.filter(submission__problem=problem, submission__is_correct=True)
        return solves.count() > 0

    def __str__(self):
        return f"{self.participant().__str__()}'s Participation in {self.contest.name}"


class ContestSubmission(models.Model):
    participation = models.ForeignKey(
        ContestParticipation, on_delete=models.CASCADE, related_name="submissions"
    )
    submission = models.OneToOneField(
        "Submission", on_delete=models.CASCADE, related_name="contest_submission"
    )
