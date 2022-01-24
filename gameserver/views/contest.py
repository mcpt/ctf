from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseBadRequest
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
    template_name = "contest/list.html"
    title = "Contests"

    def get_queryset(self):
        queryset = models.Contest.objects.order_by("-start_time")
        if self.request.user.is_authenticated:
            return queryset.filter(Q(is_private=False) | Q(organizers=self.request.user)).distinct()
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
    template_name = "contest/detail.html"

    def get_title(self):
        return "" + self.get_object().name

    def get_description(self):
        return self.get_object().summary

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["participations"] = None
        if self.request.user.is_authenticated:
            context["participations"] = self.request.user.participations_for_contest(self.get_object())
        return context

    def get_form(self):
        if self.request.user.is_authenticated:
            return forms.ContestJoinForm(
                **self.get_form_kwargs(),
            )
        else:
            return None

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["user"] = self.request.user
        cur_kwargs["contest"] = self.get_object()
        return cur_kwargs

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not self.get_object().is_ongoing:
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        if (
            self.request.user.current_contest is not None
            and self.request.user.current_contest.contest == self.get_object()
        ):
            team = form.cleaned_data["participant"]
            new_participation = models.ContestParticipation.objects.get_or_create(team=team, contest=self.get_object())[
                0
            ]
            prev_participation = self.request.user.current_contest
            if prev_participation.team is not None:
                return HttpResponseBadRequest("Cannot change from teams")
            models.ContestSubmission.objects.filter(participation=prev_participation).update(
                participation=new_participation
            )
            prev_participation.delete()
            new_participation.save()
            new_participation.participants.add(self.request.user)
            self.request.user.current_contest = new_participation
            self.request.user.save()
            return super().form_valid(form)
        else:
            team = form.cleaned_data["participant"]
            contest = self.get_object()
            if team is not None:
                contest_participation = models.ContestParticipation.objects.get_or_create(
                    team=team, contest=contest
                )[0]
            else:
                try:
                    contest_participation = models.ContestParticipation.objects.get(
                        team=None,
                        participants=self.request.user,
                        contest=contest,
                    )
                except models.ContestParticipation.DoesNotExist:
                    contest_participation = models.ContestParticipation(contest=self.get_object())
            contest_participation.save()
            if contest_participation.participants.count() == contest.max_team_size:
                return HttpResponseBadRequest(
                    "This team is already full. Please choose another team."
                )
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


class ContestProblemList(UserPassesTestMixin, ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "contest_problems"
    template_name = "contest/problem_list.html"

    def test_func(self):
        self.contest = get_object_or_404(models.Contest, slug=self.kwargs["slug"])
        return (
            self.request.in_contest and self.request.participation.contest == self.contest
        ) or self.contest.is_finished()

    def get_title(self):
        return "Problems for " + self.contest.name

    def get_queryset(self):
        return self.contest.problems.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class ContestSubmissionList(UserPassesTestMixin, ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "contest_submissions"
    template_name = "contest/submission_list.html"
    paginate_by = 50

    def test_func(self):
        self.contest = get_object_or_404(models.Contest, slug=self.kwargs["slug"])
        return (
            self.request.in_contest and self.request.participation.contest == self.contest
        ) or self.contest.is_finished()

    def get_queryset(self):
        return models.ContestSubmission.objects.filter(participation__contest=self.contest).order_by(
            "-submission__date_created"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class ContestScoreboard(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.ContestParticipation
    context_object_name = "participations"
    template_name = "contest/scoreboard.html"

    def get_queryset(self):
        self.contest = get_object_or_404(models.Contest, slug=self.kwargs["slug"])
        return self.contest.ranks()

    def get_title(self):
        return "Scoreboard for " + self.contest.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        return context


class ContestParticipationDetail(DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin):
    model = models.ContestParticipation
    context_object_name = "participation"
    template_name = "contest/participation.html"

    def get_title(self):
        return f"{self.get_object().__str__()}"

    def get_description(self):
        return self.get_object().__str__()
