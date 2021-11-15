from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q, Sum, Min, Count
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery
from django.urls import reverse
from django.conf import settings

from .choices import organization_request_status_choices, timezone_choices
from .contest import ContestParticipation
from .submission import Submission


def get_default_user_timezone():
    return settings.DEFAULT_TIMEZONE


class User(AbstractUser):
    description = models.TextField(blank=True)

    timezone = models.CharField(
        max_length=50, choices=timezone_choices, default=get_default_user_timezone
    )

    organizations = models.ManyToManyField(
        "Organization",
        blank=True,
        related_name="members",
        related_query_name="member",
    )

    payment_pointer = models.CharField(
        max_length=300,
        validators=[
            RegexValidator(
                regex=r"\$.*\.(?:.*)+?(?:/.*)?",
                message="Enter a payment pointer",
            )
        ],
        blank=True,
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

    def has_solved(self, problem):
        solves = self.submissions.filter(problem=problem, is_correct=True)
        return solves.count() > 0

    def _get_unique_correct_submissions(self):
        return self.submissions.filter(is_correct=True).values("problem", "problem__points").distinct()

    def points(self):
        points = self._get_unique_correct_submissions().aggregate(points=Coalesce(Sum("problem__points"), 0))["points"]
        return points

    def num_flags_captured(self):
        return self._get_unique_correct_submissions().count()

    def participations_for_contest(self, contest):
        return ContestParticipation.objects.filter(
            Q(participants=self), contest=contest
        )

    def remove_contest(self):
        self.current_contest = None
        self.save()

    remove_contest.alters_data = True

    def update_contest(self):
        participation = self.current_contest
        if participation is not None and participation.contest.is_finished():
            self.remove_contest()

    update_contest.alters_data = True

    @classmethod
    def ranks(cls):
        submissions_with_points = Submission.objects.filter(user=OuterRef("pk"), is_correct=True).order_by().values("problem").distinct().annotate(sub_pk=Min("pk")).values('sub_pk')
        return cls.objects.annotate(
                points=Coalesce(Sum("submission__problem__points", filter=Q(submission__in=Subquery(submissions_with_points))), 0),
                flags=Coalesce(Count("submission__pk", filter=Q(submission__in=Subquery(submissions_with_points))), 0),
            ).order_by("-points", "flags")


class Organization(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="organizations_owning"
    )
    admins = models.ManyToManyField(
        "User", related_name="organizations_maintaining"
    )
    name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=24)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    date_registered = models.DateTimeField(auto_now_add=True)

    is_private = models.BooleanField(default=False)
    access_code = models.CharField(max_length=36, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("organization_detail", args=[self.slug])

    def is_open(self):
        return not self.is_private

    def member_count(self):
        return User.objects.filter(organizations=self).count()

    is_open.boolean = True


class OrganizationRequest(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organizations_requested"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="requests"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=1, choices=organization_request_status_choices, default="p"
    )
    reason = models.TextField()

    def get_absolute_url(self):
        return reverse("organization_detail", args=[self.organization.slug])

    def __str__(self):
        return f"Request to join {self.organization.name} ({self.pk})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if (
            self.status == "a"
            and self.organization not in self.user.organizations.all()
        ):
            self.user.organizations.add(self.organization)

    def reviewed(self):
        return self.status != "p"

    reviewed.boolean = True


class Team(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="teams_owning"
    )
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    access_code = models.CharField(max_length=36)
    date_registered = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name="teams", blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="teams",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("team_detail", args=[self.pk])

    def member_count(self):
        return self.members.all().count()
