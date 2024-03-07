from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin, FormView
from django.core.cache import cache

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
    FormMixin,
    DetailView,
    mixin.MetaMixin,
    mixin.CommentMixin,
):
    model = models.Contest
    template_name = "contest/detail.html"
    context_object_name = "contest"
    form_class = forms.ContestJoinForm

    def get_title(self):
        return self.object.name

    def get_description(self):
        return self.object.summary

    def get_success_url(self):
        return self.request.path

    def test_func(self):
        return self.get_object().is_visible_by(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.is_accessible_by(request.user):
            return HttpResponseForbidden()

        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form(self):
        if self.object.is_accessible_by(self.request.user):
            return forms.ContestJoinForm(
                **self.get_form_kwargs(),
            )

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
            self.object.is_finished and self.object.is_visible_by(self.request.user)
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
            .order_by("-pk")
        )


class ContestScoreboard(SingleObjectMixin, ListView, mixin.MetaMixin):
    model = models.ContestParticipation
    template_name = "contest/scoreboard.html"

    def get_title(self):
        return "Scoreboard for " + self.object.name

    def get_queryset(self):
        cache_key = f"contest_{self.kwargs['slug']}_scoreboard"
        queryset = cache.get(cache_key)
        if not queryset or self.request.GET.get('cache_reset', '').casefold() == "yaaaa":
            queryset = self.object.ranks().prefetch_related('team', 'submissions__problem')
            cache.set(cache_key, queryset, 5 * 5)  # Cache for 5 minutes (300 seconds)
        return queryset
    
    def _get_contest(self, slug):
        cache_key = f"contest_{slug}_scoreboard_contest"
        contest = cache.get(cache_key)
        if not contest or self.request.GET.get('cache_reset', '').casefold() == "yaaaa":
            contest = get_object_or_404(models.Contest, slug=slug)
            cache.set(cache_key, contest, 5 * 5)  # Cache for 5 minutes (300 seconds)
        return contest
    
    def get(self, request, *args, **kwargs):
        self.object = self._get_contest(self.kwargs["slug"])
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
        return self.contest.cached_ranks(
            "organization_scoreboard",
            self.contest.participations.filter(participants__organizations=self.org),
        ).select_related("team")

    def get(self, request, *args, **kwargs):
        self.contest = get_object_or_404(models.Contest, slug=self.kwargs["contest_slug"])
        self.org = get_object_or_404(models.Organization, slug=self.kwargs["org_slug"])
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
        return self.object.__str__()

    def get_description(self):
        return self.object.__str__()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["recent_contest_submissions"] = self.object.submissions.order_by("-pk")[:10]

        contest_problems = self.object.contest.problems
        participant_submissions = self.object._get_unique_correct_submissions()

        context["problem_types"] = {
            ptype: {
                "total": ptype.pc,
                "solved": ptype.pcc,
            }
            for ptype in models.ProblemType.objects.annotate(
                pc=Count("problems", filter=Q(problems__in=contest_problems.values("problem"))),
                pcc=Count(
                    "problems",
                    filter=Q(
                        problems__in=contest_problems.filter(
                            submission__in=participant_submissions.values("pk")
                        ).values("problem")
                    ),
                ),
            )
        }

        if pus := contest_problems.filter(problem__problem_type=None):
            context["problem_types"]["Other"] = {
                "total": pus.count(),
                "solved": participant_submissions.filter(
                    problem__problem__problem_type=None
                ).count(),
            }

        # new queries instead of summation in case a problem has multiple problem_types
        context["problem_types_total"] = {
            "total": contest_problems.count(),
            "solved": participant_submissions.count(),
        }
        return context


class ContestParticipationSubmissionList(
    UserPassesTestMixin, SingleObjectMixin, ListView, mixin.MetaMixin
):
    template_name = "contest/submission_list.html"
    paginate_by = 50

    def get_title(self):
        return f"Submissions by {self.object.participant} in {self.object.contest}"

    def get_queryset(self):
        return self.object.submissions.select_related("problem", "participation").order_by("-pk")

    def test_func(self):
        return (
            self.request.in_contest and self.request.participation.contest == self.object.contest
        ) or (
            self.object.contest.is_finished and self.contest.object.is_visible_by(self.request.user)
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=models.ContestParticipation.objects.all())
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest_participation"] = self.object
        context["contest"] = self.object.contest
        return context
