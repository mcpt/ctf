from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.views.generic import DetailView, ListView

import gameserver.models as models

from . import mixin


class Index(ListView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "home.html"
    model = models.BlogPost
    context_object_name = "posts"

    def get_ordering(self):
        return "-date_created"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problems"] = models.Problem.objects.filter(is_public=True).order_by(
            "-date_created"
        )[:5]
        context["comments"] = models.Comment.objects.order_by("-date_created")[:5]
        moment = timezone.localtime()
        context["contests"] = models.Contest.objects.filter(
            start_time__lte=moment, end_time__gt=moment
        ).order_by("-start_time")[:5]
        return context


class BlogPost(DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin):
    model = models.BlogPost
    context_object_name = "post"
    template_name = "blogpost/detail.html"
    og_type = "article"

    def get_title(self):
        return "" + self.object.title

    def get_author(self):
        return self.object.author.all()

    def get_description(self):
        return self.object.summary


class Writeup(DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin):
    model = models.Writeup
    context_object_name = "post"
    template_name = "problem/writeup.html"
    og_type = "article"

    def get_title(self):
        return "" + self.object.title

    def get_author(self):
        return self.object.author.all()

    def get_description(self):
        return self.object.summary
