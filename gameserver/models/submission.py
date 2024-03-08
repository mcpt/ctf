from django.db import models
from django.db.models import Q

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
        "Problemlem",
        on_delete=models.CASCADE,
        related_name="submissions",
        related_query_name="submission",
    )
    is_correct = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=256, null=True, default=None)

    def __str__(self):
        return f"{self.user.username}'s submission for {self.problem.name}"

    def save(self, *args, **kwargs):
        if self.is_correct and self.problem.is_public:
            UserScore.update_or_create(user=self.user, change_in_score=self.problem.points, update_flags=True)
        return super().save(*args, **kwargs)

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
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['problem']),
            models.Index(fields=['is_correct'])
        ]
