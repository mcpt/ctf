from django.contrib import messages
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


class OrganizationDetail(DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin):
    model = models.Organization
    context_object_name = "group"
    template_name = "organization/detail.html"

    def get_title(self):
        return "Organization " + self.object.name

    def get_description(self):
        return self.object.description

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["last_user_organization_request"] = (
                models.OrganizationRequest.objects.filter(
                    organization=self.object, user=self.request.user
                )
                .order_by("-date_created")
                .first()
            )
            context["organization_requests"] = models.OrganizationRequest.objects.filter(
                organization=self.object, user=self.request.user
            ).order_by("-date_created")[:3]
        else:
            context["organization_requests"] = []
        context["entity"] = "organization"
        context["membered_admins"] = self.object.admins.filter(organizations=self.object).order_by(
            "username"
        )
        return context


class OrganizationRequest(LoginRequiredMixin, CreateView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "organization/form-join.html"
    model = models.OrganizationRequest
    fields = ["reason"]

    def form_valid(self, form):
        form.instance.organization = self.object
        form.instance.user = self.request.user
        messages.info(self.request, "Your request to join this organization has been submitted.")
        return super().form_valid(form)

    def get_object(self):
        return models.Organization.objects.get(slug=self.kwargs["slug"])

    def get_title(self):
        return "Request to join Organization " + self.object.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.object
        context["is_join_request"] = True
        return context


class OrganizationJoin(LoginRequiredMixin, FormView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "organization/form-join.html"
    form_class = forms.GroupJoinForm
    fields = ["access_code"]

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.is_public:
            self.success()
            return redirect(self.object)
        return super().post(*args, **kwargs)

    def success(self):
        self.request.user.organizations.add(self.object)

    def form_valid(self, form):
        self.success()
        messages.success(self.request, "You are now a member of this organization!")
        return super().form_valid(form)

    def get_success_url(self, *args, **kwargs):
        return self.object.get_absolute_url()

    def get_object(self):
        return models.Organization.objects.get(slug=self.kwargs["slug"])

    def get_title(self):
        return "Join Organization " + self.object.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.object
        return context

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs["group"] = self.object
        return cur_kwargs


@method_decorator(require_POST, name="dispatch")
class OrganizationLeave(LoginRequiredMixin, RedirectView):
    query_string = True
    pattern_name = "organization_detail"

    def get_redirect_url(self, *args, **kwargs):
        organization = get_object_or_404(models.Organization, slug=kwargs["slug"])
        self.request.user.organizations.remove(organization)
        messages.info(self.request, "You have left this organization.")
        return super().get_redirect_url(*args, **kwargs)
