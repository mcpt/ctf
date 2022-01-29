import hashlib
import re
import uuid

from django.db import models
from django.db.models import Q
from django.urls import reverse

from ..utils import challenge
from . import abstract
from .contest import ContestProblem
from .profile import User

# Create your models here.


class ProblemGroup(abstract.Category):
    pass


class ProblemType(abstract.Category):
    pass


class Problem(models.Model):
    flag = models.CharField(max_length=256)

    author = models.ManyToManyField(User, related_name="problems_authored", blank=True)
    name = models.CharField(max_length=128)
    description = models.TextField()
    summary = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    testers = models.ManyToManyField(User, related_name="problems_testing", blank=True)

    points = models.PositiveSmallIntegerField()

    problem_group = models.ManyToManyField(ProblemGroup, blank=True)
    problem_type = models.ManyToManyField(ProblemType, blank=True)

    is_public = models.BooleanField(default=False)

    challenge_spec = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def is_private(self):
        return not self.is_public

    @property
    def flag_format(self):
        flag_format_match = re.match(r"(.*)\{.*\}", self.flag)

        if flag_format_match is not None:
            return f"{flag_format_match.group(1)}{{}}"
        else:
            return None

    def get_absolute_url(self):
        return reverse("problem_detail", args=[self.slug])

    def get_contest_problem(self, participation):
        try:
            return ContestProblem.objects.get(problem=self, contest=participation.contest)
        except ContestProblem.DoesNotExist:
            return None

    def is_accessible_by(self, user):
        if self.is_public:
            return True

        if not user.is_authenticated:
            return False

        if (
            user.current_contest is not None
            and self.request.participation.contest.problems.filter(
                problem=self.get_object()
            ).exists()
        ):
            return True

        return self.is_editable_by(user)

    def is_editable_by(self, user):
        if user.is_superuser or user.has_perm("gameserver.edit_all_problems"):
            return True

        if user.is_authenticated:
            if self.author.filter(id=user.id).exists() or self.testers.filter(id=user.id).exists():
                return True

        return False

    @classmethod
    def get_public_problems(cls):
        return cls.objects.filter(is_public=True)

    @classmethod
    def get_visible_problems(cls, user):
        if not user.is_authenticated:
            return cls.get_public_problems()

        if user.is_superuser or user.has_perm("gameserver.edit_all_problems"):
            return cls.objects

        return cls.objects.filter(Q(is_public=True) | Q(author=user) | Q(testers=user)).distinct()

    @classmethod
    def get_editable_problems(cls, user):
        if user.is_superuser or user.has_perm("gameserver.edit_all_problems"):
            return cls.objects

        return cls.objects.filter(author=user).distinct()

    def create_challenge_instance(self, instance_owner):
        if self.challenge_spec is not None:
            return challenge.create_challenge_instance(
                self.challenge_spec, self.slug, self.flag, instance_owner
            )

    def fetch_challenge_instance(self, instance_owner):
        if self.challenge_spec is not None:
            return challenge.fetch_challenge_instance(
                self.challenge_spec, self.slug, instance_owner
            )

    def delete_challenge_instance(self, instance_owner):
        if self.challenge_spec is not None:
            return challenge.delete_challenge_instance(
                self.challenge_spec, self.slug, instance_owner
            )

    class Meta:
        permissions = (
            ("change_problem_visibility", "Change visibility of problems"),
            ("edit_all_problems", "Edit all problems"),
        )


def problem_file_path(instance, filename):
    return f"problem/{instance.problem.slug}/{filename}"


class ProblemFile(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="files")
    artifact = models.FileField(upload_to=problem_file_path, unique=True)
    checksum = models.CharField(max_length=64)

    def __str__(self):
        return self.file_name()

    def file_name(self):
        return self.artifact.name.split("/")[-1]

    def save(self, *args, **kwargs):
        hash_sha256 = hashlib.sha256()
        for chunk in self.artifact.chunks():
            hash_sha256.update(chunk)
        self.checksum = hash_sha256.hexdigest()
        super().save(*args, **kwargs)
