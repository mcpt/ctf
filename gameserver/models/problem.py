import uuid

from django.db import models
from django.urls import reverse

from . import abstract
from .profile import User

# Create your models here.


class ProblemGroup(abstract.Category):
    pass


class ProblemType(abstract.Category):
    pass


class Problem(models.Model):
    flag = models.CharField(max_length=256)

    author = models.ManyToManyField(
        User, related_name="problems_authored", blank=True
    )
    name = models.CharField(max_length=128)
    description = models.TextField()
    summary = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    points = models.PositiveSmallIntegerField()

    problem_group = models.ManyToManyField(ProblemGroup, blank=True)
    problem_type = models.ManyToManyField(ProblemType, blank=True)

    is_private = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("problem_detail", args=[self.slug])


def problem_file_path(instance, filename):
    return f"problem/{instance.problem.slug}/{filename}"


class ProblemFile(models.Model):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="files"
    )
    artifact = models.FileField(upload_to=problem_file_path, unique=True)

    def __str__(self):
        return self.file_name()

    def file_name(self):
        return self.artifact.name.split("/")[-1]
