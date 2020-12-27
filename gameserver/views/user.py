from django.views.generic.base import RedirectView
from .. import forms
from django.views.generic import DetailView, ListView
from .. import models
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.urls import reverse
from django.shortcuts import redirect
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
    template_name = "gameserver/user/list.html"
    title = "pCTF: Users"

    def get_queryset(self):
        return self.model.objects.annotate(cum_points=Sum('solves__problem__points')).order_by('-cum_points')

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect('contest_scoreboard', slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)


class UserDetail(DetailView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.User
    context_object_name = "profile"
    template_name = "gameserver/user/detail.html"
    og_type = "profile"

    def get_slug_field(self):
        return "username"

    def get_title(self):
        return "pCTF: User " + self.get_object().username

    def get_description(self):
        return self.get_object().description

    def get_author(self):
        return [self.get_object()]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_contenttype = ContentType.objects.get_for_model(models.User)
        context["comments"] = models.Comment.objects.filter(
            parent_content_type=user_contenttype, parent_object_id=self.get_object().pk
        )
        return context


class UserSolves(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "solves"
    template_name = "gameserver/user/solve.html"
    paginate_by = 50

    def get_queryset(self):
        self.user = get_object_or_404(models.User, username=self.kwargs["slug"])
        return models.Solves.objects.filter(author=self.user).order_by(
            self.get_ordering()
        )

    def get_ordering(self):
        return "-points"

    def get_title(self):
        return "pCTF: Solves by User " + self.user.username

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = self.kwargs["slug"]
        return context


class UserEdit(UpdateView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "gameserver/user/form.html"
    form_class = forms.ProfileUpdateForm
    success_url = reverse_lazy("user_detail_redirect")
    title = "pCTF: Update Profile"

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super(UpdateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
