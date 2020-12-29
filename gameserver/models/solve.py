from django.db import models
from django.urls import reverse

from .problem import Problem
from .profile import User

# Create your models here.


class Solve(models.Model):
    solver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solves",
    )
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="solves"
    )
    created = models.DateTimeField(auto_now_add=True)
    is_disqualified = models.BooleanField(default=False)

    def is_firstblood(self):
        return (
            self
            == Solve.objects.filter(problem=self.problem)
            .order_by("pk")
            .first()
        )
