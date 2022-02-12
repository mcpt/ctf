from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormView

from .. import forms, models
from . import mixin


class OrganizationList(ListView, mixin.MetaMixin):
    model = models.Organization
    template_name = "organization/list.html"
    context_object_name = "organizations"
    title = "Organizations"

    def get_ordering(self):
        return "-name"


class OrganizationDetail(DetailView, mixin.MetaMixin, mixin.CommentMixin):
    model = models.Organization
    template_name = "organization/detail.html"
    context_object_name = "group"

    def get_title(self):
        return self.object.name

    def get_description(self):
        return self.object.description

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["last_user_organization_request"] = (
                models.OrganizationRequest.objects.filter(
                    organization=self.object, user=self.request.user
                )
                .order_by("-pk")
                .first()
            )
            context["organization_requests"] = models.OrganizationRequest.objects.filter(
                organization=self.object, user=self.request.user
            ).order_by("-pk")[:3]
        else:
            context["organization_requests"] = []
        context["entity"] = "organization"
        context["membered_admins"] = self.object.admins.filter(organizations=self.object).order_by(
            "username"
        )
        return context


class OrganizationRequest(LoginRequiredMixin, CreateView, mixin.MetaMixin):
    model = models.OrganizationRequest
    template_name = "organization/form-join.html"
    fields = ["reason"]

    def get_title(self):
        return "Request to join Organization " + self.org.name

    def get_object(self):
        return get_object_or_404(models.Organization, slug=self.kwargs["slug"])

    def dispatch(self, request, *args, **kwargs):
        self.org = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.organization = self.org
        form.instance.user = self.request.user
        messages.info(self.request, "Your request to join this organization has been submitted.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.org
        context["is_join_request"] = True
        return context


class OrganizationJoin(LoginRequiredMixin, SingleObjectMixin, FormView, mixin.MetaMixin):
    template_name = "organization/form-join.html"
    form_class = forms.GroupJoinForm

    def get_title(self):
        return "Join Organization " + self.object.name

    def get_success_url(self, *args, **kwargs):
        return self.object.get_absolute_url()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=models.Organization.objects.all())
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        if self.object.is_open:
            self.success()
            return redirect(self.object)
        return super().post(*args, **kwargs)

    def success(self):
        self.request.user.organizations.add(self.object)
        messages.success(self.request, "You are now a member of this organization!")

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["group"] = self.object
        return cur_kwargs

    def form_valid(self, form):
        self.success()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.object
        return context


@method_decorator(require_POST, name="dispatch")
class OrganizationLeave(LoginRequiredMixin, RedirectView):
    pattern_name = "organization_detail"
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        organization = get_object_or_404(models.Organization, slug=kwargs["slug"])

        self.request.user.organizations.remove(organization)
        for team in self.request.user.teams_owning.all():
            team.organizations.remove(organization)

        messages.info(self.request, "You have left this organization.")
        return super().get_redirect_url(*args, **kwargs)
