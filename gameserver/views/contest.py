from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, FormMixin, FormView

from .. import forms, models
from . import mixin


class ContestList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "contests"
    template_name = "gameserver/contest/list.html"
    title = "pCTF: Contests"

    def get_queryset(self):
        queryset = models.Contest.objects.order_by("-start_time")
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(is_private=False) | Q(organizers=self.request.user)
            )
        else:
            return queryset.filter(is_private=False)


class ContestDetail(
    DetailView,
    FormMixin,
    mixin.TitleMixin,
    mixin.MetaMixin,
    mixin.CommentMixin,
):
    model = models.Contest
    context_object_name = "contest"
    template_name = "gameserver/contest/detail.html"
    form_class = forms.ContestJoinForm

    def get_title(self):
        return "pCTF: Contest " + self.get_object().name

    def get_description(self):
        return self.get_object().summary

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["participations"] = None
        if self.request.user.is_authenticated:
            context[
                "participations"
            ] = self.request.user.participations_for_contest(self.get_object())
        return context

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["user"] = self.request.user
        cur_kwargs["contest"] = self.get_object()
        return cur_kwargs

    def post(self, request, *args, **kwargs):
        if (
            not request.user.is_authenticated
            or not self.get_object().is_ongoing
        ):
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        team = form.cleaned_data["participant"]
        if team is not None:
            contest_participation = (
                models.ContestParticipation.objects.get_or_create(
                    team=team, contest=self.get_object()
                )[0]
            )
        else:
            try:
                contest_participation = (
                    models.ContestParticipation.objects.get(
                        team=None,
                        participants=self.request.user,
                        contest=self.get_object(),
                    )
                )
            except models.ContestParticipation.DoesNotExist:
                contest_participation = models.ContestParticipation(
                    contest=self.get_object()
                )
        contest_participation.save()
        contest_participation.participants.add(self.request.user)
        self.request.user.current_contest = contest_participation
        self.request.user.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path


@method_decorator(require_POST, name="dispatch")
class ContestLeave(LoginRequiredMixin, RedirectView):
    query_string = True
    pattern_name = "contest_detail"

    def get_redirect_url(self, *args, **kwargs):
        self.request.user.remove_contest()
        return super().get_redirect_url(*args, **kwargs)


class ContestProblemList(
    UserPassesTestMixin, ListView, mixin.TitleMixin, mixin.MetaMixin
):
    context_object_name = "problems"
    template_name = "gameserver/contest/problems.html"

    def test_func(self):
        self.contest = get_object_or_404(
            models.Contest, slug=self.kwargs["slug"]
        )
        return (
            self.request.in_contest
            and self.request.participation.contest == self.contest
        ) or self.contest.is_finished

    def get_title(self):
        return "pCTF: Problems for Contest " + self.contest.name

    def get_queryset(self):
        return self.contest.problems.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class ContestSolveList(
    UserPassesTestMixin, ListView, mixin.TitleMixin, mixin.MetaMixin
):
    context_object_name = "contest_solves"
    template_name = "gameserver/contest/solves.html"
    paginate_by = 50

    def test_func(self):
        self.contest = get_object_or_404(
            models.Contest, slug=self.kwargs["slug"]
        )
        return (
            self.request.in_contest
            and self.request.participation.contest == self.contest
        ) or self.contest.is_finished

    def get_queryset(self):
        return models.ContestSolve.objects.filter(
            participation__contest=self.contest
        ).order_by("-solve__created")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class ContestScoreboard(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.ContestParticipation
    context_object_name = "participations"
    template_name = "gameserver/contest/scoreboard.html"

    def get_queryset(self):
        self.contest = get_object_or_404(
            models.Contest, slug=self.kwargs["slug"]
        )
        return self.contest.ranks()

    def get_title(self):
        return "pCTF: Scoreboard for Contest " + self.contest.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class ContestParticipationDetail(
    DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin
):
    model = models.ContestParticipation
    context_object_name = "participation"
    template_name = "gameserver/contest/participation.html"

    def get_title(self):
        return f"pCTF: {self.get_object().__str__()}"

    def get_description(self):
        return self.get_object().__str__()
