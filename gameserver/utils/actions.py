import time

from django.contrib import messages

from gameserver.models import ContestScore, UserScore


def recalculate_score(self, request, queryset):
    start = time.monotonic_ns()
    for contest in queryset:
        ContestScore.reset_data(contest)

    end = time.monotonic_ns()
    messages.success(request, f"Time taken: {(end - start) / 1e9} seconds")


recalculate_score.short_description = "Recalculate scores for selected contests."


def recalculate_user_scores(self, request, queryset):
    start = time.monotonic_ns()
    UserScore.reset_data(users=queryset)
    end = time.monotonic_ns()
    messages.success(request, f"Time taken: {(end - start) / 1e9} seconds")


recalculate_user_scores.short_description = "Recalculate scores for selected users."


def recalculate_all_user_scores(self, request, queryset):
    start = time.monotonic_ns()
    UserScore.reset_data()
    end = time.monotonic_ns()
    messages.success(request, f"Time taken: {(end - start) / 1e9} seconds")


recalculate_all_user_scores.short_description = "Recalculate scores for all users. NOTE: You must select at least one user to run this action due to Django admin limitations."
