from datetime import timedelta

from django.apps import apps
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Min, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html

from gameserver.models.cache import ContestScore

from ..templatetags.common_tags import strfdelta
from . import abstract


class ContestTag(abstract.Category):
    pass


class Contest(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ContestScore = apps.get_model("gameserver", "ContestScore", require_ready=True)

    organizers = models.ManyToManyField("User", related_name="contests_organized", blank=True)
    curators = models.ManyToManyField("User", related_name="contests_curated", blank=True)
    organizations = models.ManyToManyField(
        "Organization",
        related_name="contests",
        blank=True,
        help_text="Only users of these organizations can access the contest",
    )

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField()
    summary = models.CharField(max_length=150)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    tags = models.ManyToManyField(ContestTag, blank=True)

    is_public = models.BooleanField(default=True, db_index=True)
    max_team_size = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )

    date_created = models.DateTimeField(auto_now_add=True)
    first_blood_webhook = models.URLField(
        blank=True,
        help_text="URL to send a POST request to when a user gets the first blood on a problem",
    )

    class Meta:
        permissions = (
            ("change_contest_visibility", "Change visibility of contests"),
            ("edit_all_contests", "Edit all contests"),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("contest_detail", args=[self.slug])

    @cached_property
    def is_private(self):
        return not self.is_public

    @cached_property
    def teams_allowed(self):
        return self.max_team_size is None or self.max_team_size > 1

    @cached_property
    def is_started(self):
        return self.start_time <= timezone.now()

    @cached_property
    def is_finished(self):
        return self.end_time < timezone.now()

    @cached_property
    def is_ongoing(self):
        return self.is_started and not self.is_finished

    @cached_property
    def duration(self):
        return self.end_time - self.start_time

    def has_problem(self, problem):
        if isinstance(problem, ContestProblem):
            return self.problems.filter(pk=problem.pk).exists()
        else:
            return self.problems.filter(problem__pk=problem.pk).exists()

    def ranks(self):
        return self.ContestScore.ranks(self)

    def is_visible_by(self, user):
        if self.is_public:
            return True

        if not user.is_authenticated:
            return False

        if self.organizations.filter(pk__in=user.organizations.all()).exists():
            return True

        return self.is_editable_by(user)

    def is_accessible_by(self, user):
        if not user.is_authenticated:
            return False

        if not self.is_ongoing:
            return False

        if self.organizations.filter(pk__in=user.organizations.all()).exists():
            return True

        if self.is_editable_by(user):
            return True

        return self.is_public

    def is_editable_by(self, user):
        if not user.is_authenticated:
            return False

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return True

        return (
            self.organizers.filter(pk=user.pk).exists() or self.curators.filter(pk=user.pk).exists()
        )

    @classmethod
    def get_visible_contests(cls, user):
        if not user.is_authenticated:
            return cls.objects.filter(is_public=True)

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return cls.objects.all()

        return cls.objects.filter(
            Q(is_public=True)
            | Q(organizers=user)
            | Q(curators=user)
            | Q(is_public=False, organizations__in=user.organizations.all())
        ).distinct()

    @classmethod
    def get_ongoing_contests(cls, user):
        return cls.get_visible_contests(user).filter(
            start_time__lte=timezone.now(), end_time__gt=timezone.now()
        )

    @classmethod
    def get_editable_contests(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        if user.is_superuser or user.has_perm("gameserver.edit_all_contests"):
            return cls.objects.all()

        return cls.objects.filter(Q(organizers=user) | Q(curators=user)).distinct()


class ContestParticipation(models.Model):
    cache = ContestScore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ContestScore = apps.get_model("gameserver", "ContestScore", require_ready=True)

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
        return f"{self.participant}'s Participation in {self.contest.name}"

    def get_absolute_url(self):
        return reverse("contest_participation_detail", args=[self.pk])

    @cached_property
    def participant(self):
        if self.team is None:
            return self.participants.first()
        else:
            return self.team

    def _get_unique_correct_submissions(self):
        # Switch to ContestProblem -> Problem Later
        return (
            self.submissions.filter(submission__is_correct=True)
            .select_related("problem")
            .values("problem", "problem__points")
            .distinct()
        )

    def points(self):
        return (
            self.ContestScore.objects.filter(participation=self)
            .values_list("points", flat=True)
            .get()
        )

    def flags(self):
        return (
            self.ContestScore.objects.filter(participation=self)
            .values_list("flag_count", flat=True)
            .get()
        )

    def get_rank(self):
        return self.ContestScore.ranks(participation=self)

    @cached_property
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

    @cached_property
    def last_solve_time(self):
        last_solve = self.last_solve
        if last_solve is not None:
            return last_solve.submission.date_created
        else:
            return self.contest.start_time

    @property
    def time_taken(self) -> str:
        """Returns the total amount of time the user has spent on the contest"""
        solve_time = self.last_solve_time
        return strfdelta(
            timedelta(seconds=round((solve_time - self.contest.start_time).total_seconds()))
        )

    def rank(self):
        return self.contest.ranks().filter(Q(points__gte=self.points())).count()

    def has_attempted(self, problem):
        return problem.is_attempted_by(self)

    def has_solved(self, problem):
        return problem.is_solved_by(self)

    def has_firstblooded(self, problem):
        return problem.is_firstblooded_by(self)


class ContestProblem(models.Model):
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name="problems",
        related_query_name="problem",
        db_index=True,
    )
    problem = models.ForeignKey(
        "Problem", on_delete=models.CASCADE, related_name="contests", related_query_name="contest"
    )
    points = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ("contest", "problem")

    def __str__(self):
        return f"{self.problem.name} on {self.contest.name}"

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
        db_index=True,
    )
    problem = models.ForeignKey(
        ContestProblem,
        on_delete=models.CASCADE,
        related_name="submissions",
        related_query_name="submission",
    )
    submission = models.OneToOneField(
        "Submission",
        on_delete=models.CASCADE,
        related_name="contest_submission",
        db_index=True,
    )

    def __str__(self):
        return f"{self.participation.participant}'s submission for {self.problem.problem.name} in {self.problem.contest.name}"

    def get_absolute_admin_url(self):
        url = reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=[self.id]
        )
        return format_html('<a href="{url}">{url}</a>', url=url)

    @cached_property
    def is_correct(self):
        return self.submission.is_correct

    @cached_property
    def is_firstblood(self):
        prev_correct_submissions = ContestSubmission.objects.filter(
            problem=self.problem, submission__is_correct=True, pk__lte=self.pk
        )

        return prev_correct_submissions.count() == 1 and prev_correct_submissions.first() == self

    @property
    async def ais_firstblooded(self):
        prev_correct_submissions = ContestSubmission.objects.filter(
            problem=self.problem, submission__is_correct=True, pk__lte=self.pk
        )

        return (
            await prev_correct_submissions.acount() == 1
            and await prev_correct_submissions.afirst() == self
        )

    def save(self, *args, **kwargs):
        cache.delete(
            make_template_fragment_key("participant_data", [self.participation])
        )  # see participation.html
        cache.delete(
            make_template_fragment_key("user_participation", [self.participation])
        )  # see scoreboard.html
        super().save(*args, **kwargs)
