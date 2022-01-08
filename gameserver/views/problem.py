import logging

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin
from django.http import HttpResponseForbidden

from .. import forms, models
from . import mixin

logger = logging.getLogger("django")


class ProblemList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "problems"
    template_name = "problem/list.html"
    title = "Problems"

    def get_queryset(self):
        queryset = models.Problem.objects.order_by("name")
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(is_private=False) | Q(author=self.request.user)
            ).distinct()
        else:
            return queryset.filter(is_private=False)

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect(
                "contest_problem_list", slug=request.participation.contest.slug
            )
        else:
            return super().get(request, *args, **kwargs)


class ProblemDetail(
    UserPassesTestMixin,
    DetailView,
    FormMixin,
    mixin.TitleMixin,
    mixin.MetaMixin,
    mixin.CommentMixin,
):
    model = models.Problem
    template_name = "problem/detail.html"
    form_class = forms.FlagSubmissionForm

    def get_contest_object(self):
        if self.request.in_contest:
            return self.get_object().get_contest_problem(self.request.participation)
        else:
            return None

    def test_func(self):
        return (
            not self.get_object().is_private
            or (
                self.request.in_contest
                and self.request.participation.contest.problems.filter(problem=self.get_object()).exists()
            )
            or self.request.user in self.get_object().author.all()
        )

    def get_title(self):
        return self.get_object().name

    def get_description(self):
        return self.get_object().summary

    def get_author(self):
        return self.get_object().author.all()

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["problem"] = self.get_object()
        return cur_kwargs

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def _create_submission_object(self, is_correct=False):
        submission = models.Submission.objects.create(
            user=self.request.user, problem=self.get_object(), is_correct=is_correct
        )
        if self.request.in_contest:
            models.ContestSubmission.objects.create(
                problem=self.get_contest_object(), submission=submission, participation=self.request.participation
            )
        return submission

    def form_valid(self, form):
        if (not self.request.user.has_solved(self.get_object())) or (self.request.in_contest and not self.request.participation.has_solved(self.get_contest_object())):
            messages.success(self.request, "Your flag is correct!")
        else:
            messages.info(self.request, "Your flag is correct, but you have already solved this problem.")
        self._create_submission_object(is_correct=True)
        return super().form_valid(form)

    def form_invalid(self, form):
        self._create_submission_object(is_correct=False)
        messages.error(self.request, "Your flag is incorrect.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse(
            "problem_detail", kwargs={"slug": self.get_object().slug}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest_problem"] = self.get_contest_object()
        if self.request.user.is_authenticated:
            if (self.request.user.has_solved(self.get_object())) or (self.request.in_contest and self.request.participation.has_solved(self.get_contest_object())):
                context["status"] = "solved"
            elif (self.request.user.has_attempted(self.get_object())) or (self.request.in_contest and self.request.participation.has_attempted(self.get_contest_object())):
                context["status"] = "attempted"
        return context

class ProblemSubmissionList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "submissions"
    template_name = "submission/list.html"
    paginate_by = 50

    def get_queryset(self):
        self.problem = get_object_or_404(
            models.Problem, slug=self.kwargs["slug"]
        )
        return models.Submission.objects.filter(problem=self.problem).order_by(
            self.get_ordering()
        )

    def get_ordering(self):
        return "-date_created"

    def get_title(self):
        return "Submissions for " + self.problem.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problem"] = self.problem
        return context
