from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic.edit import FormMixin
from django.urls import reverse
from .. import forms
from .. import models
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
import uuid
from . import mixin


class TeamList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Team
    context_object_name = "teams"
    template_name = "gameserver/team/list.html"
    title = "pCTF: Teams"

    def get_ordering(self):
        return "-name"


class TeamDetail(DetailView, FormMixin, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Team
    context_object_name = "team"
    template_name = "gameserver/team/detail.html"
    form_class = forms.GroupJoinForm

    def get_title(self):
        return "pCTF: Team " + self.get_object().name

    def get_description(self):
        return self.get_object().description

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_contenttype = ContentType.objects.get_for_model(models.Organization)
        context["comments"] = models.Comment.objects.filter(
            parent_content_type=user_contenttype, parent_object_id=self.get_object().pk
        )
        return context

    def get_form_kwargs(self, *args, **kwargs):
        cur_kwargs = super().get_form_kwargs(*args, **kwargs)
        cur_kwargs['group'] = self.get_object()
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
        messages.success(self.request, 'You are now a member of this team!')
        self.get_object().members.add(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('team_detail', kwargs={'pk': self.get_object().pk})


class TeamCreate(LoginRequiredMixin, CreateView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = 'gameserver/team/create.html'
    model = models.Team
    fields = ('name', 'description')

    def get_title(self):
        return 'pCTF: Create a Team'

    def form_valid(self, form, **kwargs):
        model = form.save(commit=False)
        model.owner = self.request.user
        model.access_token = uuid.uuid4().hex
        model.save()
        model.members.add(self.request.user)

        return super().form_valid(form)


class TeamEdit(UpdateView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "gameserver/team/form.html"
    title = "pCTF: Update Team"
    fields = ['name', 'description', 'access_code']
    model = models.Team


class TeamLeave(LoginRequiredMixin, RedirectView):
    query_string = True
    pattern_name = "team_detail"

    def get_redirect_url(self, *args, **kwargs):
        team = get_object_or_404(models.Team, pk=kwargs["pk"])
        team.members.remove(self.request.user)
        return super().get_redirect_url(*args, **kwargs)
