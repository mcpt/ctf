from django.db import models
from django.db.models import Q
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
        # TODO: Consider only submissions from within contest, should be implemented in ContestSubmission instead
        return (
            self
            == Submission.objects.filter(problem=self.problem, is_correct=True)
            .exclude(user__in=self.problem.author.all() | self.problem.testers.all())
            .order_by("pk")
            .first()
        )

    @classmethod
    def get_visible_submissions(cls, user):
        if not user.is_authenticated:
            return cls.objects.filter(problem__is_public=True)

        if user.is_superuser or user.has_perm("gameserver.edit_all_problems"):
            return cls.objects.all()

        if user.current_contest is None:
            return cls.objects.filter(
                Q(problem__is_public=True)
                | Q(user=user)
                | Q(problem__author=user)
                | Q(problem__testers=user)
            )
        else:
            return cls.objects.filter(
                contest_submission__participation__contest=user.current_contest.contest
            )
