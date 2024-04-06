import hashlib
import re
import secrets

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from ..utils import challenge
from . import abstract
from .contest import ContestProblem

# Create your models here.


class ProblemGroup(abstract.Category):
    pass


class ProblemType(abstract.Category):
    pass


def gen_opaque_id():
    return secrets.token_urlsafe(32)


class Problem(models.Model):
    author = models.ManyToManyField("User", related_name="problems_authored", blank=True)
    testers = models.ManyToManyField("User", related_name="problems_testing", blank=True)
    organizations = models.ManyToManyField("Organization", related_name="problems", blank=True)

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField()
    summary = models.CharField(max_length=150)

    opaque_id = models.CharField(max_length=172, default=gen_opaque_id, editable=False, unique=True)

    problem_group = models.ManyToManyField(ProblemGroup, related_name="problems", blank=True)
    problem_type = models.ManyToManyField(ProblemType, related_name="problems", blank=True)

    flag = models.CharField(max_length=256)
    points = models.PositiveSmallIntegerField()
    challenge_spec = models.JSONField(null=True, blank=True)
    log_submission_content = models.BooleanField(default=False)

    is_public = models.BooleanField(default=False, db_index=True)

    date_created = models.DateTimeField(auto_now_add=True)

    firstblood = models.ForeignKey(
        "Submission", related_name="firstblooded", null=True, blank=True, on_delete=models.PROTECT
    )

    class Meta:
        permissions = (
            ("change_problem_visibility", "Change visibility of problems"),
            ("edit_all_problems", "Edit all problems"),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("problem_detail", args=[self.slug])

    @cached_property
    def is_private(self):
        return not self.is_public

    @property
    def flag_format(self):
        flag_format_match = re.match(r"(.*)\{.*\}", self.flag)

        if flag_format_match is not None:
            return f"{flag_format_match.group(1)}{{}}"
        else:
            return None

    def contest_problem(self, contest):
        try:
            return ContestProblem.objects.get(problem=self, contest=contest)
        except ContestProblem.DoesNotExist:
            return None

    @cached_property
    def ongoing_contests_problem(self):
        now = timezone.now()
        return ContestProblem.objects.filter(
            problem=self,
            contest__start_time__lte=now,
            contest__end_time__gte=now,
        )

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

    def is_attempted_by(self, user):
        return self.submissions.filter(user=user).exists()

    def is_solved_by(self, user):
        return self.submissions.filter(user=user, is_correct=True).exists()

    def is_firstblooded_by(self, user):
        return self.firstblood.user == user if self.firstblood else False

    def is_accessible_by(self, user):
        if self.is_public:
            return True

        if not user.is_authenticated:
            return False

        if self.organizations.filter(pk__in=user.organizations.all()).exists():
            return True

        if user.current_contest is not None and user.current_contest.contest.has_problem(self):
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
            return cls.objects.all()

        return cls.objects.filter(
            Q(is_public=True)
            | Q(author=user)
            | Q(testers=user)
            | Q(organizations__in=user.organizations.all())
        ).distinct()

    @classmethod
    def get_editable_problems(cls, user):
        if user.is_superuser or user.has_perm("gameserver.edit_all_problems"):
            return cls.objects.all()

        return cls.objects.filter(author=user).distinct()


def problem_file_path(instance, filename):
    return f"problem/{instance.problem.opaque_id}/{filename}"


class ProblemFile(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="files")
    artifact = models.FileField(max_length=100 + 172, upload_to=problem_file_path, unique=True)
    checksum = models.CharField(max_length=64)

    def __str__(self):
        return self.file_name

    @property
    def file_name(self):
        return self.artifact.name.split("/")[-1]

    def save(self, *args, **kwargs):
        hash_sha256 = hashlib.sha256()
        for chunk in self.artifact.chunks():
            hash_sha256.update(chunk)
        self.checksum = hash_sha256.hexdigest()
        super().save(*args, **kwargs)
