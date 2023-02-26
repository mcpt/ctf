from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.views.generic import DetailView, ListView

import gameserver.models as models

from . import mixin


class Index(ListView, mixin.MetaMixin):
    model = models.BlogPost
    template_name = "home.html"
    context_object_name = "posts"
    ordering = "-pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problems"] = models.Problem.objects.filter(is_public=True).order_by("-pk")[:5]
        context["comments"] = models.Comment.objects.order_by("-pk")[:5]
        moment = timezone.localtime()
        context["contests"] = models.Contest.get_visible_contests(self.request.user).filter(
            start_time__lte=moment, end_time__gt=moment
        ).order_by("-start_time")[:5]
        return context


class BlogPost(DetailView, mixin.MetaMixin, mixin.CommentMixin):
    model = models.BlogPost
    template_name = "blogpost/detail.html"
    context_object_name = "post"
    og_type = "article"

    def get_title(self):
        return self.object.title

    def get_author(self):
        return self.object.author.all()

    def get_description(self):
        return self.object.summary


class Writeup(DetailView, mixin.MetaMixin, mixin.CommentMixin):
    model = models.Writeup
    template_name = "problem/writeup.html"
    context_object_name = "post"
    og_type = "article"

    def get_title(self):
        return self.object.title

    def get_author(self):
        return self.object.author.all()

    def get_description(self):
        return self.object.summary
