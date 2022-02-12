from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Count, F, Min, OuterRef, Q, Subquery, Sum
from django.db.models.expressions import Window
from django.db.models.functions import Coalesce, Rank
from django.urls import reverse

from .choices import organization_request_status_choices, timezone_choices
from .contest import ContestParticipation, ContestProblem, ContestSubmission
from .problem import Problem
from .submission import Submission


def get_default_user_timezone():
    return settings.DEFAULT_TIMEZONE


class User(AbstractUser):
    full_name = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)

    school_name = models.CharField(
        max_length=80, blank=True, help_text="The full name of your school"
    )

    school_contact = models.EmailField(
        blank=True,
        verbose_name="teacher contact email",
        help_text="Email address of a school teacher for verification purposes",
    )

    timezone = models.CharField(
        max_length=50, choices=timezone_choices, default=get_default_user_timezone
    )

    organizations = models.ManyToManyField(
        "Organization",
        blank=True,
        related_name="members",
        related_query_name="member",
    )

    current_contest = models.ForeignKey(
        "ContestParticipation",
        on_delete=models.SET_NULL,
        related_name="current_participants",
        null=True,
        blank=True,
    )

    def get_absolute_url(self):
        return reverse("user_detail", args=[self.username])

    def _get_unique_correct_submissions(self, queryset=None):
        if queryset is None:
            queryset = self.submissions.filter(is_correct=True, problem__is_public=True)

        return queryset.values("problem", "problem__points").distinct()

    def points(self, queryset=None):
        return self._get_unique_correct_submissions(queryset).aggregate(
            points=Coalesce(Sum("problem__points"), 0)
        )["points"]

    def flags(self, queryset=None):
        return (
            self._get_unique_correct_submissions(queryset).filter(problem__is_public=True).count()
        )

    def rank(self, queryset=None):
        return User.ranks(queryset).get(pk=self.pk).rank

    @classmethod
    def ranks(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()

        submissions_with_points = (
            Submission.objects.filter(user=OuterRef("pk"), is_correct=True, problem__is_public=True)
            .order_by()
            .values("problem")
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
            )
            .annotate(
                rank=Window(
                    expression=Rank(),
                    order_by=F("points").desc(),
                )
            )
            .order_by("rank", "flags")
        )

    def has_attempted(self, problem):
        if isinstance(problem, ContestProblem):
            return problem.is_attempted_by(self.participation_for_contest(problem.contest))
        elif isinstance(problem, Problem):
            if self.current_contest is not None:
                contest_problem = problem.contest_problem(self.current_contest.contest)
                if contest_problem is not None:
                    return self.current_contest.has_attempted(contest_problem)

            return problem.is_attempted_by(self)
        else:
            raise TypeError("problem must be a Problem or ContestProblem")

    def has_solved(self, problem):
        if isinstance(problem, ContestProblem):
            return problem.is_solved_by(self.participation_for_contest(problem.contest))
        elif isinstance(problem, Problem):
            if self.current_contest is not None:
                contest_problem = problem.contest_problem(self.current_contest.contest)
                if contest_problem is not None:
                    return self.current_contest.has_solved(contest_problem)

            return problem.is_solved_by(self)
        else:
            raise TypeError("problem must be a Problem or ContestProblem")

    def has_firstblooded(self, problem):
        if isinstance(problem, ContestProblem):
            return problem.is_firstblooded_by(self.participation_for_contest(problem.contest))
        elif isinstance(problem, Problem):
            if self.current_contest is not None:
                contest_problem = problem.contest_problem(self.current_contest.contest)
                if contest_problem is not None:
                    return self.current_contest.has_firstblooded(contest_problem)

            return problem.is_firstblooded_by(self)
        else:
            raise TypeError("problem must be a Problem or ContestProblem")

    def participation_for_contest(self, contest):
        try:
            return ContestParticipation.objects.get(participants=self, contest=contest)
        except ContestParticipation.DoesNotExist:
            return None

    def remove_contest(self):
        self.current_contest = None
        self.save()

    remove_contest.alters_data = True

    def update_contest(self):
        participation = self.current_contest
        if participation is not None and participation.contest.is_finished:
            self.remove_contest()

    update_contest.alters_data = True


class Organization(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="organizations_owning")
    admins = models.ManyToManyField("User", related_name="organizations_maintaining")

    name = models.CharField(max_length=64)
    slug = models.SlugField(unique=True)
    short_name = models.CharField(max_length=24)
    description = models.TextField(blank=True)

    is_open = models.BooleanField(default=True)
    access_code = models.CharField(max_length=36, blank=True)

    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (("edit_all_organizations", "Edit all organizations"),)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("organization_detail", args=[self.slug])

    @property
    def member_count(self):
        return User.objects.filter(organizations=self).count()

    def ranks(self):
        return User.ranks(queryset=self.members)

    def is_editable_by(self, user):
        if user.is_superuser or user.has_perm("gameserver.edit_all_organizations"):
            return True

        if user.is_authenticated:
            if self.owner == user or self.admins.filter(pk=user.pk).exists():
                return True

        return False

    @classmethod
    def get_editable_organizations(cls, user):
        if user.is_superuser or user.has_perm("gameserver.edit_all_organizations"):
            return cls.objects.all()

        return cls.objects.filter(owner=user).distinct()


class OrganizationRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organizations_requested")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="requests"
    )
    reason = models.TextField()

    status = models.CharField(
        max_length=1, choices=organization_request_status_choices, default="p"
    )

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request to join {self.organization.name} ({self.pk})"

    def get_absolute_url(self):
        return reverse("organization_detail", args=[self.organization.slug])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == "a" and self.organization not in self.user.organizations.all():
            self.user.organizations.add(self.organization)

    @property
    @admin.display(boolean=True)
    def reviewed(self):
        return self.status != "p"


class Team(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="teams_owning")

    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    members = models.ManyToManyField(User, related_name="teams", blank=True)
    organizations = models.ManyToManyField(
        Organization,
        blank=True,
        related_name="teams",
        related_query_name="team",
    )

    access_code = models.CharField(max_length=36)

    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("team_detail", args=[self.pk])

    @property
    def member_count(self):
        return self.members.all().count()

    def participation_for_contest(self, contest):
        try:
            return ContestParticipation.objects.get(team=self, contest=contest)
        except ContestParticipation.DoesNotExist:
            return None
