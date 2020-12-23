from django.db import models
import uuid
from .profile import User

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ProblemCategory(Category):
    pass


class ProblemType(Category):
    pass


class Problem(models.Model):
    flag = models.CharField(max_length=256)

    author = models.ManyToManyField(User, related_name="problems_authored", blank=True)
    name = models.CharField(max_length=128)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    points = models.PositiveSmallIntegerField()

    category = models.ManyToManyField(ProblemCategory, blank=True)
    problem_type = models.ManyToManyField(ProblemType, blank=True)

    def __str__(self):
        return self.name

def problem_file_path(instance, filename):
    return f'problem/{instance.problem.slug}/{filename}'

class ProblemFile(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="files")
    artifact = models.FileField(upload_to=problem_file_path, unique=True)

    def __str__(self):
        return self.name

    def file_name(self):
        return '.'.join(self.artifact.name.split(".")[-2:])
