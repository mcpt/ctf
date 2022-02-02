from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView

from .. import forms, models
from . import mixin


class UserDetailRedirect(RedirectView):
    pattern_name = "user_detail"
    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        return reverse(self.pattern_name, args=[user.username])


class UserList(ListView, mixin.MetaMixin):
    model = models.User
    template_name = "user/list.html"
    context_object_name = "users"
    title = "Users"

    def get_queryset(self):
        return models.User.ranks()

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect("contest_scoreboard", slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)


class UserDetail(DetailView, mixin.MetaMixin, mixin.CommentMixin):
    model = models.User
    slug_field = "username"
    template_name = "user/detail.html"
    context_object_name = "profile"
    og_type = "profile"

    def get_title(self):
        return "User " + self.object.username

    def get_description(self):
        return self.object.description

    def get_author(self):
        return [self.object]


class UserSubmissionList(SingleObjectMixin, ListView, mixin.MetaMixin):
    slug_field = "username"
    template_name = "submission/list.html"
    paginate_by = 50

    def get_title(self):
        return "Submissions by User " + self.object.username

    def get_queryset(self):
        return (
            models.Submission.get_visible_submissions(self.request.user)
            .filter(user=self.object)
            .order_by("-pk")
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=models.User.objects.all())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = self.object
        context["hide_pk"] = True
        return context


class UserEdit(UpdateView, mixin.MetaMixin):
    form_class = forms.ProfileUpdateForm
    template_name = "user/form.html"
    success_url = reverse_lazy("user_detail_redirect")
    title = "Update Profile"

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(UpdateView, self).get_form_kwargs()
        kwargs["profile"] = self.request.user
        return kwargs
