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

from .. import forms, models
from . import mixin

logger = logging.getLogger("django")


class ProblemList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "problems"
    template_name = "gameserver/problem/list.html"
    title = "Problems"

    def get_queryset(self):
        queryset = models.Problem.objects.order_by("name")
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(is_private=False) | Q(author=self.request.user)
            )
        else:
            return queryset.filter(is_private=False)

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect(
                "contest_problems", slug=request.participation.contest.slug
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
    template_name = "gameserver/problem/detail.html"
    form_class = forms.FlagSubmissionForm

    def test_func(self):
        return (
            not self.get_object().is_private
            or (
                self.request.in_contest
                and self.get_object()
                in self.request.user.current_contest.contest.problems.all()
            )
            or self.request.user in self.get_object().author.all()
        )

    def get_title(self):
        return "" + self.get_object().name

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

    def form_valid(self, form):
        if self.request.user.has_solved(self.get_object()):
            message = "Your flag was correct, but you have already solved this problem."
            messages.info(self.request, message)
        else:
            messages.success(self.request, "Your flag was correct!")
            solve = models.Solve.objects.create(
                solver=self.request.user, problem=self.get_object()
            )
            if self.request.in_contest:
                models.ContestSolve.objects.create(
                    solve=solve, participation=self.request.participation
                )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "problem_detail", kwargs={"slug": self.get_object().slug}
        )


class ProblemSolves(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "solves"
    template_name = "gameserver/problem/solves.html"
    paginate_by = 50

    def get_queryset(self):
        self.problem = get_object_or_404(
            models.Problem, slug=self.kwargs["slug"]
        )
        return models.Solve.objects.filter(problem=self.problem).order_by(
            self.get_ordering()
        )

    def get_ordering(self):
        return "-created"

    def get_title(self):
        return "Solves for Problem " + self.problem.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problem"] = self.problem
        return context
