from django.views.generic import DetailView, ListView
from .. import models
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
import logging
from . import mixin

logger = logging.getLogger("django")


class ProblemList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Problem
    context_object_name = "problems"
    template_name = "gameserver/problem/list.html"
    title = "pCTF: Problems"

    def get_ordering(self):
        return "name"


class ProblemDetail(DetailView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Problem
    context_object_name = "problem"
    template_name = "gameserver/problem/detail.html"

    def get_title(self):
        return "pCTF: " + self.get_object().name

    def get_description(self):
        return self.get_object().description

    def get_author(self):
        return self.get_object().author.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem_contenttype = ContentType.objects.get_for_model(models.Problem)
        context["comments"] = models.Comment.objects.filter(
            parent_content_type=problem_contenttype,
            parent_object_id=self.get_object().pk,
        )
        return context


class ProblemAllSubmissions(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "submissions"
    template_name = "gameserver/problem/all_submission.html"
    paginate_by = 50

    def get_queryset(self):
        self.problem = get_object_or_404(models.Problem, slug=self.kwargs["slug"])
        return models.Submission.objects.filter(problem=self.problem).order_by(
            self.get_ordering()
        )

    def get_ordering(self):
        return "-created"

    def get_title(self):
        return "pCTF: All Submissions for Problem " + self.problem.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problem"] = self.problem
        return context


class ProblemBestSubmissions(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "submissions"
    template_name = "gameserver/problem/best_submission.html"
    paginate_by = 50

    def get_queryset(self):
        self.problem = get_object_or_404(models.Problem, slug=self.kwargs["slug"])
        return models.Submission.objects.filter(problem=self.problem).order_by(
            self.get_ordering()
        )

    def get_ordering(self):
        return "-points"

    def get_title(self):
        return "pCTF: Best Submissions for Problem " + self.problem.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problem"] = self.problem
        return context
