from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional, Protocol, Self

from django.apps import apps
from django.db import models, transaction
from django.db.models import (
    BooleanField,
    Case,
    Count,
    F,
    QuerySet,
    Sum,
    Value,
    When,
    Window,
)
from django.db.models.functions import Coalesce, Rank
from django.http import HttpRequest
from django.utils import timezone

if TYPE_CHECKING:
    from .contest import Contest, ContestParticipation, ContestSubmission
    from .profile import User

EPOCH_TIME = datetime(1971, 1, 1, 0, 0, 0)


class ResetableCache(Protocol):
    def can_reset(cls, request: HttpRequest) -> None:
        ...


class CacheMeta(models.Model):
    class Meta:
        abstract = True
        permissions = [
            (
                "can_reset_cache",
                "Designates if the user has permission to reset the scoring caches or not.",
            )
        ]

    @classmethod
    def _can_reset(cls, request: HttpRequest):
        return all(
            [
                request.user.is_authenticated,
                request.user.is_staff,
                request.GET.get("reset", "").casefold() == "true",
            ]
        )


class UserScore(CacheMeta):
    user = models.OneToOneField(
        "User", related_name="score_cache", on_delete=models.CASCADE, db_index=True
    )
    points = models.PositiveIntegerField(help_text="The amount of points.", default=0)
    flag_count = models.PositiveIntegerField(
        help_text="The amount of flags the user/team has.", default=0
    )
    last_correct_submission = models.DateTimeField(
        help_text="The date of the last correct submission.",
        # auto_now=True, auto now is not used as it does not allow you to override the value
        editable=False,
        blank=True,
        default=EPOCH_TIME,  # only used for migration (overwritten by reset_score)
    )

    @classmethod
    def should_reset(cls, request: HttpRequest):
        return cls._can_reset(request) and request.user.has_perm(
            "gameserver.can_reset_cache_user_score"
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
                order_by=("-points", "-last_correct_submission"),
            )
        ).order_by("rank")
        return qs

    @classmethod
    def update_or_create(cls, change_in_score: int, user: "User", update_flags: bool = True):
        assert change_in_score > 0
        queryset = cls.objects.filter(user=user)

        if not queryset.exists():  # no user found matching that
            cls.objects.create(
                user=user,
                flag_count=int(update_flags),
                points=change_in_score,
                last_correct_submission=timezone.now(),
            )
            return cls.update_or_create(
                change_in_score=change_in_score, user=user, update_flags=update_flags
            )

        if update_flags:
            queryset.update(
                points=F("points") + change_in_score,
                flag_count=F("flag_count") + 1,
                last_correct_submission=timezone.now(),
            )
        else:
            queryset.update(
                points=F("points") + change_in_score, last_correct_submission=timezone.now()
            )

    @classmethod
    def get_rank(cls, user: "User") -> int:
        """
        Get the rank of a user
        
        There are a couple issues with implementing this function as
        cls.ranks().get(user=user).rank
        - The biggest is django is lazy and the user's rank will always be 1
        The only way I see to implement this would be to use raw SQL (see cls.ranks().query)
        """
        raise NotImplementedError
        
    @classmethod
    def reset_data(cls, users: Optional[QuerySet["User"]] = None):
        from django.contrib.auth import get_user_model
        from gameserver.models import Submission

        if users is None:
            users = get_user_model().objects.all()
            cls.objects.all().delete()  # clear past objs
        else:
            cls.objects.filter(user__in=users).delete()  # clear past objs

        scores_to_create = []

        for user in users:
            queryset = user._get_unique_correct_submissions()
            queryset = queryset.aggregate(
                points=Coalesce(Sum("problem__points"), 0),
                flags=Count("problem"),
            )
            try:
                last_correct_submission = (
                    Submission.objects.filter(user=user, problem__is_public=True, is_correct=True)
                    .latest("date_created")
                    .date_created
                )
            except Submission.DoesNotExist:  # user have never submitted to a public problem
                last_correct_submission = EPOCH_TIME

            scores_to_create.append(
                UserScore(
                    user=user,
                    flag_count=queryset["flags"],
                    points=queryset["points"],
                    last_correct_submission=last_correct_submission,
                )
            )
        # Use bulk_create to create all objects in a single query
        cls.objects.bulk_create(scores_to_create)


class ContestScore(CacheMeta):
    participation = models.OneToOneField(
        "ContestParticipation", related_name="score_cache", on_delete=models.CASCADE, db_index=True
    )
    points = models.PositiveIntegerField(help_text="The amount of points.", default=0)
    flag_count = models.PositiveIntegerField(
        help_text="The amount of flags the user/team has.", default=0
    )

    last_correct_submission = models.DateTimeField(
        help_text="The date of the last correct submission.",
        # auto_now=True, auto now is not used as it does not allow you to override the value
        editable=False,
        blank=True,
        default=EPOCH_TIME,  # only used for migration (overwritten by reset_score)
    )

    # contest_id = models.IntegerField(
    #     help_text="The id for which contest this applies to. Do not change this value manually.",
    #     blank=True,
    #     null=False,
    # )

    # def save(self, *args, **kwargs):
    #     self.contest_id = self.participation.contest_id
    #     super().save(*args, **kwargs)

    @classmethod
    def should_reset(cls, request: HttpRequest):
        return cls._can_reset(request) and request.user.has_perm(
            "gameserver.can_reset_cache_user_score"
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
        contest: Optional["Contest"] = None,
        participation: (
            Optional["ContestParticipation"] | Optional[QuerySet["ContestParticipation"]]
        ) = None,
    ) -> models.QuerySet:
        assert (
            contest is None or participation is None
        ), "You must set either contest or participation"
        # contest_content_type = ContentType.objects.get_for_model(apps.get_model("gameserver", "Contest"))
        # perm_edit_all_contests = Permission.objects.get(
        #     codename="edit_all_contests", content_type=contest_content_type
        # )
        if participation:
            if isinstance(participation, QuerySet):
                query = cls.objects.filter(participation__in=participation)
            else:
                query = cls.objects.filter(participation=participation)
        else:
            if isinstance(contest, int):
                query = cls.objects.filter(participation__contest_id=contest)
            else:
                query = cls.objects.filter(participation__contest=contest)
        query = query.prefetch_related("participation")  # .exclude(
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
            rank=Window(
                expression=Rank(),
                order_by=("-points", "-last_correct_submission"),
            ),
        ).order_by("rank")
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
        assert change_in_score > 0, "change_in_score must be greater than 0"
        queryset = cls.objects.filter(participation=participant)

        if not queryset.exists():  # no user/team found matching that
            cls.objects.create(
                participation=participant,
                flag_count=int(update_flags),
                points=change_in_score,
                last_correct_submission=timezone.now(),
            )

        with transaction.atomic():
            queryset.select_for_update()  # prevent race conditions with other team members

            if update_flags:
                queryset.update(
                    points=F("points") + change_in_score,
                    flag_count=F("flag_count") + 1,
                    last_correct_submission=timezone.now(),
                )
            else:
                queryset.update(
                    points=F("points") + change_in_score, last_correct_submission=timezone.now()
                )
    @classmethod
    def reset_data(cls, contest: Optional["Contest"] = None, all: bool = False):
        assert contest is not None or all, "Either contest or all must be set to True"
        ContestModel = apps.get_model("gameserver", "Contest")
        ContestSubmissionModel: ContestSubmission = apps.get_model(
            "gameserver", "ContestSubmission"
        )
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
            try:
                last_correct_submission = (
                    ContestSubmissionModel.objects.filter(
                        problem__contest=contest,
                        participation=participant,
                        problem__problem__is_public=True,
                        submission__is_correct=True,
                    )
                    .prefetch_related("submission")
                    .latest("submission__date_created")
                    .submission.date_created
                )
            except (
                ContestSubmissionModel.DoesNotExist
            ):  # user have never submitted to a public problem
                last_correct_submission = EPOCH_TIME
            scores_to_create.append(
                ContestScore(
                    participation=participant,
                    flag_count=queryset["flags"],
                    points=queryset["points"],
                    last_correct_submission=last_correct_submission,
                )
            )
        # Use bulk_create to create all objects in a single query
        cls.objects.bulk_create(scores_to_create)
