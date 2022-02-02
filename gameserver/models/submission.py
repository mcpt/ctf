from django.db import models
from django.db.models import F, Q
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
    is_correct = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    @property
    def is_firstblood(self):
        prev_correct_submissions = Submission.objects.filter(
            problem=self.problem, is_correct=True, pk__lte=self.pk
        ).exclude(
            Q(problem__author=F("user"))
            | Q(problem__testers=F("user"))
            | Q(problem__organizations__member=F("user"))
        )

        return prev_correct_submissions.count() == 1 and prev_correct_submissions.first() == self

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
                | Q(problem__organizations__member=user)
            ).distinct()
        else:
            return cls.objects.filter(
                contest_submission__participation__contest=user.current_contest.contest
            )
