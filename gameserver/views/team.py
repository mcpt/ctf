import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, FormMixin, FormView, UpdateView

from .. import forms, models
from . import mixin


class TeamList(ListView, mixin.MetaMixin):
    model = models.Team
    template_name = "team/list.html"
    context_object_name = "teams"
    title = "Teams"

    def get_ordering(self):
        return "-name"


class TeamDetail(
    DetailView,
    FormMixin,
    mixin.MetaMixin,
    mixin.CommentMixin,
):
    model = models.Team
    template_name = "team/detail.html"
    context_object_name = "group"
    form_class = forms.GroupJoinForm

    def get_title(self):
        return "Team " + self.object.name

    def get_description(self):
        return self.object.description

    def get_success_url(self):
        return reverse("team_detail", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["group"] = self.object
        return cur_kwargs

    def form_valid(self, form):
        messages.success(self.request, "You are now a member of this team!")
        self.object.members.add(self.request.user)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Your access code is incorrect.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entity"] = "team"
        return context


class TeamCreate(LoginRequiredMixin, CreateView, mixin.MetaMixin):
    model = models.Team
    template_name = "team/create.html"
    fields = ("name", "description")

    def get_title(self):
        return "Create a Team"

    def form_valid(self, form, **kwargs):
        model = form.save(commit=False)
        model.owner = self.request.user
        model.access_code = uuid.uuid4().hex
        model.save()
        model.members.add(self.request.user)

        messages.info(
            self.request,
            f"Successfully created team {model.name}! The access code to join this team is {model.access_code}; you can change this by editing the team.",
        )
        return super().form_valid(form)


class TeamEdit(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView,
    mixin.MetaMixin,
):
    model = models.Team
    template_name = "team/form.html"
    form_class = forms.TeamUpdateForm
    title = "Update Team"

    def test_func(self):
        return self.get_object().owner == self.request.user


@method_decorator(require_POST, name="dispatch")
class TeamLeave(LoginRequiredMixin, RedirectView):
    pattern_name = "team_detail"
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        team = get_object_or_404(models.Team, pk=kwargs["pk"])
        team.members.remove(self.request.user)
        messages.info(self.request, "You have left this team.")
        return super().get_redirect_url(*args, **kwargs)
