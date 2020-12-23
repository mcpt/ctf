from django.db import models
from django.urls import reverse
from .profile import User
from .problem import Problem

# Create your models here.


class Submission(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    flag = models.CharField(max_length=256)
    is_correct = models.BooleanField()
    is_first_blood = models.BooleanField()

    def get_absolute_url(self):
        return reverse("submission_detail", args=[self.pk])
