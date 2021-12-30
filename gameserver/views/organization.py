from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, FormView

from .. import forms, models
from . import mixin


class OrganizationList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Organization
    context_object_name = "organizations"
    template_name = "organization/list.html"
    title = "Organizations"

    def get_ordering(self):
        return "-name"


class OrganizationDetail(
    DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin
):
    model = models.Organization
    context_object_name = "organization"
    template_name = "organization/detail.html"

    def get_title(self):
        return "Organization " + self.get_object().name

    def get_description(self):
        return self.get_object().description

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member_count"] = self.get_object().member_count()
        if self.request.user.is_authenticated:
            context[
                "organization_requests"
            ] = models.OrganizationRequest.objects.filter(
                organization=self.get_object(), user=self.request.user
            ).order_by(
                "-date_created"
            )[
                :3
            ]
        else:
            context["organization_requests"] = []
        return context


class OrganizationMemberList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Organization
    context_object_name = "users"
    template_name = "organization/member.html"

    def get_ordering(self):
        return "-username"

    def get_queryset(self):
        self.organization = get_object_or_404(
            models.Organization, slug=self.kwargs["slug"]
        )
        return models.User.objects.filter(
            organizations=self.organization
        ).order_by(self.get_ordering())

    def get_title(self):
        return "Members of Organization " + self.organization.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.organization
        return context


@method_decorator(require_POST, name="dispatch")
class OrganizationRequest(
    LoginRequiredMixin, CreateView, mixin.TitleMixin, mixin.MetaMixin
):
    template_name = "organization/form.html"
    model = models.OrganizationRequest
    fields = ["reason"]

    def form_valid(self, form):
        form.instance.organization = self.get_object()
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_object(self):
        return models.Organization.objects.get(slug=self.kwargs["slug"])

    def get_title(self):
        return "Request to join Organization " + self.get_object().name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_object()
        return context


@method_decorator(require_POST, name="dispatch")
class OrganizationJoin(
    LoginRequiredMixin, FormView, mixin.TitleMixin, mixin.MetaMixin
):
    template_name = "organization/form.html"
    form_class = forms.GroupJoinForm
    fields = ["access_code"]

    def post(self, *args, **kwargs):
        if not self.get_object().is_private:
            self.success()
            return redirect(self.get_object())
        return super().post(*args, **kwargs)

    def success(self):
        self.request.user.organizations.add(self.get_object())

    def form_valid(self, form):
        self.success()
        return super().form_valid(form)

    def get_success_url(self, *args, **kwargs):
        return self.get_object().get_absolute_url()

    def get_object(self):
        return models.Organization.objects.get(slug=self.kwargs["slug"])

    def get_title(self):
        return "Join Organization " + self.get_object().name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_object()
        return context

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["group"] = self.get_object()
        return cur_kwargs


@method_decorator(require_POST, name="dispatch")
class OrganizationLeave(LoginRequiredMixin, RedirectView):
    query_string = True
    pattern_name = "organization_detail"

    def get_redirect_url(self, *args, **kwargs):
        organization = get_object_or_404(
            models.Organization, slug=kwargs["slug"]
        )
        self.request.user.organizations.remove(organization)
        return super().get_redirect_url(*args, **kwargs)
