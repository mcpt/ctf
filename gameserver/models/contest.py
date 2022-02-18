import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, F, Max, Min, OuterRef, Q, Subquery, Sum
from django.db.models.expressions import Window
from django.db.models.functions import Coalesce, Rank
from django.urls import reverse
from django.utils import timezone

from . import abstract

# Create your models here.


class ContestTag(abstract.Category):
    pass


class Contest(models.Model):
    organizers = models.ManyToManyField("User", related_name="contests_organized", blank=True)
    organizations = models.ManyToManyField("Organization", related_name="contests", blank=True)

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    summary = models.CharField(max_length=150)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    tags = models.ManyToManyField(ContestTag, blank=True)

    is_public = models.BooleanField(default=True)
    max_team_size = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )

    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ("change_contest_visibility", "Change visibility of contests"),
            ("edit_all_contests", "Edit all contests"),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("contest_detail", args=[self.slug])

    @property
    def is_private(self):
        return not self.is_public

    @property
    def teams_allowed(self):
        return self.max_team_size is None or self.max_team_size > 1

    @property
    def is_started(self):
        return self.start_time <= timezone.now()

    @property
    def is_finished(self):
        return self.end_time < timezone.now()

    @property
    def is_ongoing(self):
        return self.is_started and not self.is_finished

    @property
    def duration(self):
        return self.end_time - self.start_time

    def has_problem(self, problem):
        if isinstance(problem, ContestProblem):
            return self.problems.filter(pk=problem.pk).exists()
        else:
            return self.problems.filter(problem__pk=problem.pk).exists()

    def ranks(self, queryset=None):
        if queryset is None:
            queryset = self.participations.all()

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
        return (
            queryset.annotate(
                points=Coalesce(
                    Sum(
                        "submission__problem__points",
                        filter=Q(submission__in=Subquery(submissions_with_points)),
                    ),
                    0,
                ),
                flags=Coalesce(
                    Count(
                        "submission__pk", filter=Q(submission__in=Subquery(submissions_with_points))
                    ),
                    0,
                ),
                most_recent_solve_time=Coalesce(
                    Max(
                        "submission__submission__date_created",
                        filter=Q(submission__in=Subquery(submissions_with_points)),
                    ),
                    self.start_time,
                ),
            )
            .annotate(
                rank=Window(
                    expression=Rank(),
                    order_by=[F("points").desc(), F("most_recent_solve_time").asc()],
                )
            )
            .order_by("rank", "flags")
        )

    def is_visible_by(self, user):
        if self.is_public:
            return True

        if self.organizations.filter(pk__in=user.organizations.all()).exists():
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

        return cls.objects.filter(
            Q(is_public=True) | Q(organizers=user) | Q(organizations__in=user.organizations.all())
        ).distinct()

    @classmethod
    def get_editable_contests(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return cls.objects.all()

        return cls.objects.filter(organizers=user)


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

    def __str__(self):
        return f"{self.participant.__str__()}'s Participation in {self.contest.name}"

    def get_absolute_url(self):
        return reverse("contest_participation_detail", args=[self.pk])

    @property
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

    def points(self):
        points = self._get_unique_correct_submissions().aggregate(
            points=Coalesce(Sum("problem__points"), 0)
        )["points"]
        return points

    def flags(self):
        return self._get_unique_correct_submissions().count()

    @property
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

    @property
    def last_solve_time(self):
        last_solve = self.last_solve
        if last_solve is not None:
            return last_solve.submission.date_created
        else:
            return self.contest.start_time

    @property
    def time_taken(self):
        solve_time = self.last_solve_time
        return timedelta(seconds=round((solve_time - self.contest.start_time).total_seconds()))

    def rank(self):
        if isinstance(self.points, int):
            points = self.points
        else:
            points = self.points()

        return (
            self.contest.ranks()
            .filter(
                Q(points__gt=points)
                | Q(points=points, most_recent_solve_time__lt=self.last_solve_time)
            )
            .distinct()
            .count()
            + 1
        )

    def has_attempted(self, problem):
        return problem.is_attempted_by(self)

    def has_solved(self, problem):
        return problem.is_solved_by(self)

    def has_firstblooded(self, problem):
        return problem.is_firstblooded_by(self)


class ContestProblem(models.Model):
    problem = models.ForeignKey(
        "Problem", on_delete=models.CASCADE, related_name="contests", related_query_name="contest"
    )
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name="problems", related_query_name="problem"
    )
    points = models.PositiveSmallIntegerField()

    def get_absolute_url(self):
        return reverse("problem_detail", args=[self.problem.slug])

    def is_attempted_by(self, participation):
        return self.submissions.filter(participation=participation).exists()

    def is_solved_by(self, participation):
        return self.submissions.filter(
            participation=participation, submission__is_correct=True
        ).exists()

    def is_firstblooded_by(self, participation):
        if not self.is_solved_by(participation):
            return False

        participation_first_correct_submission = (
            self.submissions.filter(participation=participation, submission__is_correct=True)
            .order_by("pk")
            .first()
        )

        prev_correct_submissions = self.submissions.filter(
            submission__is_correct=True, pk__lte=participation_first_correct_submission.pk
        )

        return (
            prev_correct_submissions.count() == 1
            and prev_correct_submissions.first() == participation_first_correct_submission
        )


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

    @property
    def is_correct(self):
        return self.submission.is_correct

    @property
    def is_firstblood(self):
        prev_correct_submissions = ContestSubmission.objects.filter(
            problem=self.problem, submission__is_correct=True, pk__lte=self.pk
        )

        return prev_correct_submissions.count() == 1 and prev_correct_submissions.first() == self
