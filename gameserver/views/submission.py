from django.views.generic import DetailView, ListView
from .. import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import UserPassesTestMixin
from . import mixin


class SubmissionList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Submission
    context_object_name = "submissions"
    template_name = "gameserver/submission/list.html"
    paginate_by = 50
    title = "pCTF: Submissions"

    def get_ordering(self):
        return "-created"


class SubmissionDetail(DetailView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Submission
    context_object_name = "submission"
    template_name = "gameserver/submission/detail.html"

    def get_title(self):
        return "pCTF: Submission #" + str(self.get_object().pk)

    def get_author(self):
        return [self.get_object().author]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission_contenttype = ContentType.objects.get_for_model(models.Submission)
        context["comments"] = models.Comment.objects.filter(
            parent_content_type=submission_contenttype,
            parent_object_id=self.get_object().pk,
        )
        context["source_viewable"] = self.get_object().author == self.request.user or (
            self.request.user.is_authenticated
            and self.request.user.has_solved(self.get_object().problem)
        )
        return context
