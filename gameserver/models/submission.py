from django.core.cache import cache
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.urls import reverse


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

    def __str__(self):
        return f"{self.user.username}'s submission for {self.problem.name}"

    @property
    def is_firstblood(self):
        return self.problem.firstblood == self

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
                | Q(problem__organizations__pk__in=user.organizations.all())
            ).distinct()
        else:
            return cls.objects.filter(
                contest_submission__participation__contest=user.current_contest.contest
            )

def invalidate_total_points_cache(sender, instance, created, **kwargs):
    # TODO: only invalidate on change
    instance.user.cache_points = None
    instance.user.cache_flags = None

post_save.connect(invalidate_total_points_cache, sender=Submission)
