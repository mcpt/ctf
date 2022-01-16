from django.db import models
from django.urls import reverse

# Create your models here.


class Submission(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submissions",
        related_query_name="submission",
    )
    problem = models.ForeignKey(
        "Problem",
        on_delete=models.CASCADE,
        related_name="submissions",
        related_query_name="submission",
    )
    date_created = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)

    def is_firstblood(self):
        return self == Submission.objects.filter(problem=self.problem, is_correct=True).order_by("pk").first()
