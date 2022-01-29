from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView

from .. import models
from . import mixin


class SubmissionList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "submissions"
    template_name = "submission/list.html"
    paginate_by = 50
    title = "Submissions"

    def get_queryset(self):
        return models.Submission.get_visible_submissions(self.request.user).order_by(
            "-date_created"
        )

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect("contest_submission_list", slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)
