from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin, FormView

from .. import forms, models
from . import mixin


class ContestList(ListView, mixin.MetaMixin):
    template_name = "contest/list.html"
    context_object_name = "contests"
    title = "Contests"

    def get_queryset(self):
        return models.Contest.get_visible_contests(self.request.user).order_by("-start_time")


class ContestDetail(
    UserPassesTestMixin,
    DetailView,
    FormMixin,
    mixin.MetaMixin,
    mixin.CommentMixin,
):
    model = models.Contest
    template_name = "contest/detail.html"
    context_object_name = "contest"

    def get_title(self):
        return "" + self.object.name

    def get_description(self):
        return self.object.summary

    def get_success_url(self):
        return self.request.path

    def test_func(self):
        return self.get_object().is_visible_by(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.is_authenticated or not self.object.is_ongoing:
            return HttpResponseForbidden()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

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
        cur_kwargs["contest"] = self.object
        return cur_kwargs

    def form_valid(self, form):
        team = form.cleaned_data["participant"]
        if self.request.in_contest and self.request.user.current_contest.contest == self.object:
            contest_participation = models.ContestParticipation.objects.get_or_create(
                team=team, contest=self.object
            )[0]
            models.ContestSubmission.objects.filter(
                participation=self.request.user.current_contest
            ).update(participation=contest_participation)

            self.request.user.current_contest.delete()
        else:
            if team is not None:
                contest_participation = models.ContestParticipation.objects.get_or_create(
                    team=team, contest=self.object
                )[0]
            else:
                try:
                    contest_participation = models.ContestParticipation.objects.get(
                        team=None,
                        participants=self.request.user,
                        contest=self.object,
                    )
                except models.ContestParticipation.DoesNotExist:
                    contest_participation = models.ContestParticipation(contest=self.object)
                    contest_participation.save()

        contest_participation.participants.add(self.request.user)

        self.request.user.current_contest = contest_participation
        self.request.user.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["user_accessible"] = self.object.is_accessible_by(self.request.user)
            context["user_participation"] = self.request.user.participation_for_contest(self.object)
            context["team_participant_count"] = {
                team_pk: participant_count
                for team_pk, participant_count in self.request.user.teams.annotate(
                    participant_count=Count(
                        "contest_participations__participants",
                        filter=Q(contest_participations__contest=self.object),
                    )
                ).values_list("pk", "participant_count")
            }
        context["top_participations"] = self.object.ranks()[:10]
        return context


@method_decorator(require_POST, name="dispatch")
class ContestLeave(LoginRequiredMixin, RedirectView):
    pattern_name = "contest_detail"
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        self.request.user.remove_contest()
        return super().get_redirect_url(*args, **kwargs)


class ContestDetailsMixin(UserPassesTestMixin, SingleObjectMixin):
    def test_func(self):
        self.object = self.get_object(queryset=models.Contest.objects.all())
        return (self.request.in_contest and self.request.participation.contest == self.object) or (
            self.object.is_finished() and self.object.is_accessible_by(self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.object
        return context


class ContestProblemList(ContestDetailsMixin, ListView, mixin.MetaMixin):
    template_name = "contest/problem_list.html"

    def get_title(self):
        return "Problems for " + self.object.name

    def get_queryset(self):
        return self.object.problems.select_related("problem")


class ContestSubmissionList(ContestDetailsMixin, ListView, mixin.MetaMixin):
    template_name = "contest/submission_list.html"
    paginate_by = 50

    def get_queryset(self):
        return (
            models.ContestSubmission.objects.filter(participation__contest=self.object)
            .select_related("problem", "participation")
            .order_by("-submission__pk")
        )


class ContestScoreboard(SingleObjectMixin, ListView, mixin.MetaMixin):
    model = models.ContestParticipation
    template_name = "contest/scoreboard.html"

    def get_title(self):
        return "Scoreboard for " + self.object.name

    def get_queryset(self):
        return self.object.ranks().select_related("team")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=models.Contest.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.object
        return context


class ContestOrganizationScoreboard(ListView, mixin.MetaMixin):
    model = models.ContestParticipation
    template_name = "contest/scoreboard.html"

    def get_title(self):
        return self.org.short_name + " Scoreboard for " + self.contest.name

    def get_queryset(self):
        return self.contest.ranks(
            queryset=self.contest.participations.filter(participants__organizations=self.org)
        ).select_related("team")

    def get(self, request, *args, **kwargs):
        self.contest = models.Contest.objects.get(slug=self.kwargs["contest_slug"])
        self.org = models.Organization.objects.get(slug=self.kwargs["org_slug"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest"] = self.contest
        context["org"] = self.org
        return context


class ContestParticipationDetail(DetailView, mixin.MetaMixin, mixin.CommentMixin):
    model = models.ContestParticipation
    template_name = "contest/participation.html"
    context_object_name = "participation"

    def get_title(self):
        return f"{self.object.__str__()}"

    def get_description(self):
        return self.object.__str__()
