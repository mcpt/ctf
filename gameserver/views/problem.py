import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin

from .. import forms, models
from . import mixin

logger = logging.getLogger("django")


def int_list(l):
    return list(map(int, filter(lambda x: x.isnumeric(), l)))


class ProblemList(ListView, mixin.MetaMixin):
    template_name = "problem/list.html"
    context_object_name = "problems"
    paginate_by = 50
    title = "Practice Problems"

    def get_queryset(self):
        q = (
            models.Problem.get_visible_problems(self.request.user)
            .prefetch_related("problem_type", "problem_group")
            .filter(
                Q(problem_type__in=self.selected_types) if len(self.selected_types) else Q(),
                (
                    Q(problem_group__in=self.selected_groups)
                    if len(self.selected_groups) and not self.request.in_contest
                    else Q()
                ),
            )
            .distinct()
            .order_by("points", "name")
        )
        if self.hide_solved and self.request.user.is_authenticated:
            q = q.exclude(
                submission__in=self.request.user.submissions.filter(is_correct=True).all()
            )
        if self.nfts:
            q = q.filter(name__contains=self.nfts)
        return q

    def get(self, request, *args, **kwargs):
        self.selected_types = int_list(request.GET.getlist("type"))
        self.selected_groups = int_list(request.GET.getlist("group"))
        self.show_groups = request.GET.get("show_groups", False) == "1"
        self.hide_solved = request.GET.get("hide_solved", False) == "1"
        self.nfts = request.GET.get("nfts", None)

        if request.in_contest:
            return redirect("contest_problem_list", slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problem_filters"] = {
            "type": {
                "options": list(models.ProblemType.objects.all()),
                "selected": self.selected_types,
                "size": min(len(models.ProblemType.objects.all()), 6),
            },
            "group": {
                "options": list(models.ProblemGroup.objects.all()),
                "selected": self.selected_groups,
                "size": min(len(models.ProblemGroup.objects.all()), 4),
            },
        }

        context["show_filter"] = True
        context["show_groups"] = self.show_groups
        context["hide_solved"] = self.hide_solved
        return context


class ProblemDetail(
    UserPassesTestMixin,
    DetailView,
    FormMixin,
    mixin.MetaMixin,
    mixin.CommentMixin,
):
    model = models.Problem
    template_name = "problem/detail.html"
    form_class = forms.FlagSubmissionForm

    def get_title(self):
        return self.object.name

    def get_description(self):
        return self.object.summary

    def get_author(self):
        return self.object.author.all()

    def get_success_url(self):
        return reverse("problem_detail", kwargs={"slug": self.object.slug})

    def get_contest_object(self):
        if self.request.in_contest:
            return self.object.contest_problem(self.request.participation.contest)
        else:
            return None

    def test_func(self):
        return self.get_object().is_accessible_by(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.contest_object = self.get_contest_object()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def _create_submission_object(self, form, is_correct=None):
        if is_correct is None:
            raise TypeError("is_correct must be supplied")
        kwargs = {}
        if self.object.log_submission_content:
            kwargs["content"] = form.data["flag"]
        submission = models.Submission.objects.create(
            user=self.request.user,
            problem=self.object,
            is_correct=is_correct,
            **kwargs,
        )
        if is_correct and self.object.firstblood is None:
            self.object.firstblood = submission
        if self.contest_object is not None:
            models.ContestSubmission.objects.create(
                problem=self.contest_object,
                submission=submission,
                participation=self.request.participation,
            )
            models.ContestScore.update_or_create(
                participant=self.request.participation,
                change_in_score=self.object.points,
                update_flags=True,
            )
            if is_correct:
                pass
        return submission

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["problem"] = self.object
        return cur_kwargs

    def form_valid(self, form):
        if (not self.request.user.has_solved(self.object)) or (
            self.contest_object is not None
            and not self.request.participation.has_solved(self.contest_object)
        ):
            messages.success(self.request, "Your flag is correct!")
        else:
            messages.info(
                self.request, "Your flag is correct, but you have already solved this problem."
            )
        self._create_submission_object(form, is_correct=True)
        return super().form_valid(form)

    def form_invalid(self, form):
        self._create_submission_object(form, is_correct=False)
        messages.error(self.request, "Your flag is incorrect.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contest_problem"] = self.contest_object
        context["ongoing_contests"] = models.Contest.get_ongoing_contests(self.request.user)
        return context


class ProblemChallenge(LoginRequiredMixin, SingleObjectMixin, View):
    model = models.Problem
    raise_exception = True

    def get_instance_owner(self):
        problem = self.object
        if problem.challenge_spec is None:
            return "nobody"
        if problem.challenge_spec["perTeam"] is False:
            return "everyone"
        if self.request.in_contest and self.request.participation.contest.has_problem(self.object):
            return f"cp-{self.request.participation.pk}"
        else:
            return f"user-{self.request.user.pk}"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            self.object.fetch_challenge_instance(self.get_instance_owner()), safe=False
        )

    def post(self, request, *args, **kwargs):
        if self.object.is_accessible_by(request.user):
            return JsonResponse(
                self.object.create_challenge_instance(self.get_instance_owner()), safe=False
            )
        else:
            return HttpResponseForbidden()

    def delete(self, request, *args, **kwargs):
        instance_owner = self.get_instance_owner()
        if self.object.is_accessible_by(request.user) and (
            instance_owner != "everyone" or request.user.is_superuser
        ):
            self.object.delete_challenge_instance(instance_owner)
            return JsonResponse(None, safe=False)
        else:
            return HttpResponseForbidden()


class ProblemSubmissionList(SingleObjectMixin, ListView, mixin.MetaMixin):
    template_name = "submission/list.html"
    paginate_by = 50

    def get_title(self):
        return "Submissions for " + self.object.name

    def get_queryset(self):
        qs = (
            models.Submission.get_visible_submissions(self.request.user)
            .filter(problem=self.object)
            .select_related("user")
            .order_by("-pk")
        )
        if self.request.in_contest and self.request.participation.contest.has_problem(self.object):
            return qs.filter(
                contest_submission__participation__contest=self.request.participation.contest
            )
        else:
            return qs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=models.Problem.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problem"] = self.object
        if self.request.in_contest and self.request.participation.contest.has_problem(self.object):
            context["contest"] = self.request.participation.contest
        return context
