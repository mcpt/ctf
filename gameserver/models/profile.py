from django.db import models
from .choices import timezone_choices, organization_request_status_choices
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.urls import reverse


class User(AbstractUser):
    description = models.TextField(blank=True)

    timezone = models.CharField(max_length=50, choices=timezone_choices, default="UTC")

    organizations = models.ManyToManyField(
        "Organization", blank=True, related_name="members", related_query_name="member"
    )

    points = models.FloatField(default=0)
    num_problems_solved = models.PositiveIntegerField(default=0)

    payment_pointer = models.CharField(
        max_length=300,
        validators=[
            RegexValidator(
                regex=r"\$.*\.(?:.*)+?(?:/.*)?", message="Enter a payment pointer"
            )
        ],
        blank=True,
    )

    def get_absolute_url(self):
        return reverse("user_detail", args=[self.username])

    def has_attempted(self, problem):
        queryset = self.submission_set.filter(problem=problem)
        return bool(queryset)

    def has_solved(self, problem):
        submissions = self.submission_set.filter(problem=problem)
        for i in submissions:
            if i.scoreable is None:
                continue
            if i.scored == i.scoreable:
                return True
        return False

    def calculate_points(self):
        submissions = self.submission_set.all()
        points = {}
        for i in submissions:
            if not i.points:
                continue
            elif i.problem.pk in points:
                points[i.problem.pk] = max(points[i.problem.pk], i.points)
            else:
                points[i.problem.pk] = i.points
        return sum(points.values())

    def calculate_num_problems_solved(self):
        solved_problems = set()
        submissions = self.submission_set.all()
        for i in submissions:
            if i.scored == i.scoreable and i.problem.name not in solved_problems:
                solved_problems.add(i.problem.name)
        return len(solved_problems)

    def update_stats(self):
        self.points = self.calculate_points()
        self.num_problems_solved = self.calculate_num_problems_solved()

    def save(self, *args, **kwargs):
        self.update_stats()
        super().save(*args, **kwargs)


class Organization(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="organizations_owning"
    )
    admins = models.ManyToManyField("User", related_name="organizations_maintaining")
    name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=24)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    registered_date = models.DateTimeField(auto_now_add=True)

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
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=1, choices=organization_request_status_choices, default="p"
    )
    reason = models.TextField()

    def get_absolute_url(self):
        return reverse("organization", args=[self.organization.slug])

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
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    registered_date = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name="teams_participating_in")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="teams", blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("team_detail", args=[self.slug])

    def member_count(self):
        return self.members.all().count()
