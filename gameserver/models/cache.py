from typing import TYPE_CHECKING, Self, Optional

from django.apps import apps
from django.db import models, transaction
from django.db.models import (
    Count,
    F,
    Sum,
    Window,
    Value,
    When,
    BooleanField,
    Case,
    Q,
    OuterRef,
    Subquery,
)
from django.db.models.functions import Coalesce, Rank, DenseRank, RowNumber

from .contest import Contest, ContestParticipation, ContestSubmission

if TYPE_CHECKING:
    from .profile import User


class UserScore(models.Model):
    user = models.OneToOneField("User", on_delete=models.CASCADE, db_index=True)
    points = models.PositiveIntegerField(help_text="The amount of points.", default=0)
    flag_count = models.PositiveIntegerField(
        help_text="The amount of flags the user/team has.", default=0
    )

    def __str__(self) -> str:
        return self.user.username

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    @classmethod
    def ranks(cls):
        qs = cls.objects.annotate(
            rank=Window(
                expression=Rank(),
                order_by=F("points").desc(),
            )
        ).order_by("rank", "flag_count")
        return qs

    @classmethod
    def update_or_create(cls, change_in_score: int, user: "User", update_flags: bool = True):
        assert change_in_score > 0
        queryset = cls.objects.filter(user=user)

        if not queryset.exists():  # no user found matching that
            cls.objects.create(user=user, flag_count=int(update_flags), points=change_in_score)
            return cls.update_or_create(
                change_in_score=change_in_score, user=user, update_flags=update_flags
            )

        if update_flags:
            queryset.update(points=F("points") + change_in_score)
        else:
            queryset.update(points=F("points") + change_in_score, flag_count=F("flag_count") + 1)

    @classmethod
    def invalidate(cls, user: "User"):
        try:
            cls.objects.get(user=user).delete()
        except cls.DoesNotExist:
            pass  # user was not found.

    @classmethod
    def get(cls, user: "User") -> Self | None:
        obj = cls.objects.filter(user=user)
        if obj is None:
            return None
        return obj.first()

    @classmethod
    def reset_data(cls):
        from django.contrib.auth import get_user_model

        cls.objects.all().delete()  # clear inital objs
        UserModel = get_user_model()
        users = UserModel.objects.all()
        scores_to_create = []
        for user in users:
            queryset = user._get_unique_correct_submissions()
            queryset = queryset.aggregate(
                points=Coalesce(Sum("problem__points"), 0),
                flags=Count("problem"),
            )
            scores_to_create.append(
                UserScore(user=user, flag_count=queryset["flags"], points=queryset["points"])
            )
        # Use bulk_create to create all objects in a single query
        cls.objects.bulk_create(scores_to_create)


class ContestScore(models.Model):
    participation = models.OneToOneField(
        "ContestParticipation", on_delete=models.CASCADE, db_index=True
    )
    points = models.PositiveIntegerField(help_text="The amount of points.", default=0)
    flag_count = models.PositiveIntegerField(
        help_text="The amount of flags the user/team has.", default=0
    )

    def get_absolute_url(self):
        return self.participation.get_absolute_url()

    def time_taken(self):
        return self.participation.time_taken

    def contest(self):
        return self.participation.contest

    @classmethod
    def ranks(
        cls,
        contest: "Contest",
        queryset: Optional[models.QuerySet] = None,
        participation: Optional["ContestParticipation"] = None,
    ) -> models.QuerySet:
        assert (
            queryset is None or participation is None
        ), "Only one of queryset or participation can be set"
        # contest_content_type = ContentType.objects.get_for_model(apps.get_model("gameserver", "Contest"))
        # perm_edit_all_contests = Permission.objects.get(
        #     codename="edit_all_contests", content_type=contest_content_type
        # )
        max_submission_time_subquery = (
            ContestSubmission.objects.filter(participation=OuterRef("participation"))
            .order_by("-submission__date_created")
            .values("submission__date_created")[:1]
        )
        query = cls.objects.filter(participation__contest=contest).prefetch_related(
            "participation"
        )  # .exclude(
        #     Q(participants__is_superuser=True)
        #     | Q(participants__groups__permissions=perm_edit_all_contests)
        #     | Q(participants__user_permissions=perm_edit_all_contests)
        #     | Q(participants__in=contest.organizers.all())
        #     | Q(participants__in=contest.curators.all())
        # )
        data = query.annotate(
            is_solo=Case(
                When(participation__team_id=None, then=Value(False)),
                default=Value(True),
                output_field=BooleanField(),
            ),
            sub_rank=Window(
                expression=Rank(),
                order_by=F("points").desc(),
            ),
            rank=Window(
                expression=RowNumber(),
                order_by=F("points").desc(),
            ),
            max_submission_time=Subquery(max_submission_time_subquery),
        ).order_by("rank", "flag_count", "-max_submission_time")
        if queryset is not None:
            data = data.filter(participation__in=queryset)
        return data

    def __str__(self) -> str:
        # todo optimize by using select_related
        # self.objects.select_related("participation__team__name")
        if self.participation.team is None:
            return self.participation.participants.first().username
        return self.participation.team.name

    @classmethod
    def update_or_create(
        cls, change_in_score: int, participant: "ContestParticipation", update_flags: bool = True
    ):
        assert change_in_score > 0
        queryset = cls.objects.filter(participation=participant)

        if not queryset.exists():  # no user/team found matching that
            cls.objects.create(
                participation=participant, flag_count=int(update_flags), points=change_in_score
            )
            return cls.update_or_create(
                change_in_score=change_in_score, participant=participant, update_flags=update_flags
            )

        with transaction.atomic():
            queryset.select_for_update()  # prevent race conditions with other team members

            if update_flags:
                queryset.update(points=F("points") + change_in_score)
            else:
                queryset.update(
                    points=F("points") + change_in_score, flag_count=F("flag_count") + 1
                )

    @classmethod
    def invalidate(cls, participant: "ContestParticipation"):
        try:
            cls.objects.get(participant=participant).delete()
        except cls.DoesNotExist:
            pass  # participant was not found.

    @classmethod
    def get(cls, participant: "ContestParticipation") -> Self | None:
        obj = cls.objects.filter(participant=participant)
        if obj is None:
            return None
        return obj.first()

    @classmethod
    def reset_data(cls, contest: Optional["Contest"] = None, all: bool = False):
        assert contest is not None or all, "Either contest or all must be set to True"
        ContestModel = apps.get_model("gameserver", "Contest")
        if all:
            contests = ContestModel.objects.all()
            for contest in contests:
                cls.reset_data(contest=contest)
            return

        cls.objects.filter(participation__contest=contest).delete()  # clear past objs
        participants = contest.participations.all()
        scores_to_create = []
        for participant in participants:
            queryset = participant._get_unique_correct_submissions()
            queryset = queryset.aggregate(
                points=Coalesce(Sum("problem__points"), 0),
                flags=Count("problem"),
            )
            scores_to_create.append(
                ContestScore(
                    participation=participant,
                    flag_count=queryset["flags"],
                    points=queryset["points"],
                )
            )
        # Use bulk_create to create all objects in a single query
        cls.objects.bulk_create(scores_to_create)
