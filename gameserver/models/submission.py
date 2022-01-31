from django.db import models
from django.db.models import Case, Count, F, OuterRef, Q, Subquery, When
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

        if (
            self.user == self.problem.author
            or self.problem.testers.filter(pk=self.user.pk).exists()
        ):
            return False

        return not Submission.objects.filter(
            problem=self.problem,
            is_correct=True,
            pk__lt=self.pk,
        ).exists()

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

    @classmethod
    def get_submissions_with_status(cls, user, queryset=None):
        # TODO: Allow this method to work properly in a contest

        if queryset is None:
            queryset = cls.get_visible_submissions(user)

        return queryset.annotate(
            prev_correct_submission=Subquery(
                cls.objects.filter(
                    problem=OuterRef("problem"),
                    is_correct=True,
                    pk__lt=OuterRef("pk"),
                )
                .exclude(
                    Q(user=F("problem__author")) | Q(user=F("problem__testers")),
                )
                .values("pk")[:1]
            ),
        ).annotate(
            is_firstblood=Case(
                When(prev_correct_submission=None, then=True),
                default=False,
            ),
        )
