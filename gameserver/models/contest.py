import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, Max, Min, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from . import abstract

# Create your models here.


class ContestTag(abstract.Category):
    pass


class Contest(models.Model):
    organizers = models.ManyToManyField("User", related_name="contests_organized", blank=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    summary = models.CharField(max_length=150)
    date_created = models.DateTimeField(auto_now_add=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    tags = models.ManyToManyField(ContestTag, blank=True)

    is_public = models.BooleanField(default=True)

    max_team_size = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return self.name

    @property
    def is_private(self):
        return not self.is_public

    @property
    def teams_allowed(self):
        return self.max_team_size is None or self.max_team_size > 1

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
        submissions_with_points = (
            ContestSubmission.objects.filter(
                participation=OuterRef("pk"), submission__is_correct=True
            )
            .order_by()
            .values("submission__problem")
            .distinct()
            .annotate(sub_pk=Min("pk"))
            .values("sub_pk")
        )
        return self.participations.annotate(
            points=Coalesce(
                Sum(
                    "submission__problem__points",
                    filter=Q(submission__in=Subquery(submissions_with_points)),
                ),
                0,
            ),
            flags=Coalesce(
                Count("submission__pk", filter=Q(submission__in=Subquery(submissions_with_points))),
                0,
            ),
            most_recent_solve_time=Coalesce(
                Max(
                    "submission__submission__date_created",
                    filter=Q(submission__in=Subquery(submissions_with_points)),
                ),
                self.start_time,
            ),
        ).order_by("-points", "most_recent_solve_time", "flags")

    def is_visible_by(self, user):
        if self.is_public:
            return True

        return self.is_editable_by(user)

    def is_accessible_by(self, user):
        if not user.is_authenticated:
            return False

        return self.is_visible_by(user)

    def is_editable_by(self, user):
        if not user.is_authenticated:
            return False

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return True

        return self.organizers.filter(pk=user.pk).exists()

    @classmethod
    def get_visible_contests(cls, user):
        if not user.is_authenticated:
            return cls.objects.filter(is_public=True)

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return cls.objects.all()

        return cls.objects.filter(Q(is_public=True) | Q(organizers=user))

    @classmethod
    def get_editable_contests(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return cls.objects.all()

        return cls.objects.filter(organizers=user)

    class Meta:
        permissions = (
            ("change_contest_visibility", "Change visibility of contests"),
            ("edit_all_contests", "Edit all contests"),
        )


class ContestParticipation(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name="participations")
    is_disqualified = models.BooleanField(default=False)

    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        related_name="contest_participations",
        null=True,
        blank=True,
    )

    participants = models.ManyToManyField("User", related_name="contest_participations", blank=True)

    def participant(self):
        if self.team is None:
            return self.participants.first()
        else:
            return self.team

    def _get_unique_correct_submissions(self):
        # Switch to ContestProblem -> Problem Later
        return (
            self.submissions.filter(submission__is_correct=True)
            .values("submission__problem", "problem__points")
            .distinct()
        )

    def calc_points(self):
        points = self._get_unique_correct_submissions().aggregate(
            points=Coalesce(Sum("problem__points"), 0)
        )["points"]
        return points

    def num_flags_captured(self):
        return self._get_unique_correct_submissions().count()

    def last_solve(self):
        submissions = (
            self.submissions.filter(submission__is_correct=True)
            .order_by()
            .values("submission__problem")
            .distinct()
            .annotate(sub_pk=Min("pk"))
            .values("sub_pk")
            .order_by("-sub_pk")
        )
        if submissions.count() >= 1:
            return ContestSubmission.objects.get(pk=submissions[0]["sub_pk"])
        else:
            return None

    def last_solve_time(self):
        last_solve = self.last_solve()
        if last_solve is not None:
            print(last_solve.submission.date_created)
            return last_solve.submission.date_created
        else:
            return self.contest.start_time

    def time_taken(self):
        solve_time = self.last_solve_time()
        print(type(solve_time - self.contest.start_time))
        return solve_time - self.contest.start_time

    def rank(self):
        points = self.calc_points()
        last_solve_time = self.last_solve_time()
        contest_ranks = self.contest.ranks()
        return contest_ranks.filter(
            Q(points__gt=points) | Q(most_recent_solve_time__lte=last_solve_time, points=points)
        ).count()

    def get_absolute_url(self):
        return reverse("contest_participation_detail", args=[self.pk])

    def has_solved(self, contest_problem=None, problem=None):
        qs = self.submissions.filter(submission__is_correct=True)
        if contest_problem is not None:
            return qs.filter(problem=contest_problem).exists()
        elif problem is not None:
            return qs.filter(problem__problem=problem).exists()
        else:
            raise ValueError("Either contest_problem or problem must be specified")

    def has_attempted(self, contest_problem=None, problem=None):
        if contest_problem is not None:
            return self.submissions.filter(problem=contest_problem).exists()
        elif problem is not None:
            return self.submissions.filter(problem__problem=problem).exists()
        else:
            raise ValueError("Either contest_problem or problem must be specified")

    def __str__(self):
        return f"{self.participant().__str__()}'s Participation in {self.contest.name}"


class ContestProblem(models.Model):
    problem = models.ForeignKey(
        "Problem", on_delete=models.CASCADE, related_name="contests", related_query_name="contest"
    )
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="problems", related_query_name="problem"
    )
    points = models.PositiveSmallIntegerField()


class ContestSubmission(models.Model):
    participation = models.ForeignKey(
        ContestParticipation,
        on_delete=models.CASCADE,
        related_name="submissions",
        related_query_name="submission",
    )
    problem = models.ForeignKey(
        ContestProblem,
        on_delete=models.CASCADE,
        related_name="submissions",
        related_query_name="submission",
    )
    submission = models.OneToOneField(
        "Submission", on_delete=models.CASCADE, related_name="contest_submission"
    )
