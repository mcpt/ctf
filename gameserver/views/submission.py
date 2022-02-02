from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView

from .. import models
from . import mixin


class SubmissionList(ListView, mixin.MetaMixin):
    template_name = "submission/list.html"
    context_object_name = "submissions"
    paginate_by = 50
    title = "Submissions"

    def get_queryset(self):
        return (
            models.Submission.get_visible_submissions(self.request.user)
            .only("pk", "is_correct", "problem", "user", "date_created")
            .select_related("user", "problem")
            .order_by("-pk")
        )

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect("contest_submission_list", slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)
