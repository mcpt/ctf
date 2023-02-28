from typing import Optional

from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce


class UserCache(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="caches",
    )

    participation = models.ForeignKey(
        "ContestParticipation",
        on_delete=models.SET_NULL,
        related_name="current_caches",
        null=True,
        blank=True,
    )

    points = models.IntegerField("Points")

    flags = models.IntegerField("Flags")

    class Meta:
        unique_together = ('user', 'participation')

    def __str__(self) -> str:
        return f'{self.user} {"global" if self.participation is None else participation}'

    @classmethod
    def get(cls, user: "User", participation: Optional["ContestParticipation"]) -> "UserCache":
        assert user is not None
        print('get', user, participation)
        q = cls.objects.filter(user=user, participation=participation)
        if not q:
            obj = cls.fill_cache(user, participation)
            obj.save()
            return obj
        else:
            return q.get()

    @classmethod
    def invalidate(cls, user: "User", participation: Optional["ContestParticipation"]) -> None:
        assert user is not None
        print('invalidate', user, participation)
        q = cls.objects.filter(user=user, participation=participation)
        obj = cls.fill_cache(user, participation)
        if not q:
            obj.save()
        else:
            q.update(points=obj.points, flags=obj.flags)

    @classmethod
    def fill_cache(cls, user: "User", participation: Optional["ContestParticipation"]) -> "UserCache":
        assert user is not None
        print('fill_cache', user, participation)
        if participation is None:
            queryset = user._get_unique_correct_submissions().filter(problem__is_public=True)
        else:
            queryset = participation._get_unique_correct_submissions()
        queryset = queryset.aggregate(
            points=Coalesce(Sum("problem__points"), 0),
            flags=Count("problem"),
        )
        return UserCache(
            user=user,
            participation=participation,
            **{key: queryset[key] for key in ("points", "flags")}
        )
