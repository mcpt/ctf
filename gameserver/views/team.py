from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.generic.edit import FormMixin
from django.urls import reverse
from .. import forms
from .. import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
import uuid
from . import mixin


class TeamList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Team
    context_object_name = "teams"
    template_name = "gameserver/team/list.html"
    title = "pCTF: Teams"

    def get_ordering(self):
        return "-name"


class TeamDetail(DetailView, FormMixin, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin):
    model = models.Team
    context_object_name = "team"
    template_name = "gameserver/team/detail.html"
    form_class = forms.GroupJoinForm

    def get_title(self):
        return "pCTF: Team " + self.get_object().name

    def get_description(self):
        return self.get_object().description

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
        model.access_code = uuid.uuid4().hex
        model.save()
        model.members.add(self.request.user)

        return super().form_valid(form)


class TeamEdit(LoginRequiredMixin, UserPassesTestMixin, UpdateView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "gameserver/team/form.html"
    title = "pCTF: Update Team"
    model = models.Team
    form_class = forms.TeamUpdateForm

    def test_func(self):
        return self.get_object().owner == self.request.user

    def get_form_kwargs(self):
        kwargs = super(UpdateView, self).get_form_kwargs()
        kwargs["team"] = self.get_object()
        return kwargs

    def get_success_url(self):
        return self.get_object().get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class TeamLeave(LoginRequiredMixin, RedirectView):
    query_string = True
    pattern_name = "team_detail"

    def get_redirect_url(self, *args, **kwargs):
        team = get_object_or_404(models.Team, pk=kwargs["pk"])
        team.members.remove(self.request.user)
        return super().get_redirect_url(*args, **kwargs)
