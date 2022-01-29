from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import UpdateView

from .. import forms, models
from . import mixin


class UserDetailRedirect(RedirectView):
    permanent = False
    query_string = False
    pattern_name = "user_detail"

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        return reverse(self.pattern_name, args=[user.username])


class UserList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.User
    context_object_name = "users"
    template_name = "user/list.html"
    title = "Users"

    def get_queryset(self):
        return models.User.ranks()

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect("contest_scoreboard", slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)


class UserDetail(DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin):
    model = models.User
    context_object_name = "profile"
    template_name = "user/detail.html"
    og_type = "profile"

    def get_slug_field(self):
        return "username"

    def get_title(self):
        return "User " + self.get_object().username

    def get_description(self):
        return self.get_object().description

    def get_author(self):
        return [self.get_object()]


class UserSubmissionList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "submissions"
    template_name = "submission/list.html"
    paginate_by = 50

    def get_queryset(self):
        self.user = get_object_or_404(models.User, username=self.kwargs["slug"])
        return models.Submission.get_visible_submissions(self.request.user).filter(user=self.user).order_by("-pk")

    def get_title(self):
        return "Submissions by User " + self.user.username

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = self.kwargs["slug"]
        context["hide_pk"] = True
        return context


class UserEdit(UpdateView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "user/form.html"
    form_class = forms.ProfileUpdateForm
    success_url = reverse_lazy("user_detail_redirect")
    title = "Update Profile"

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(UpdateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
