import gameserver.models as models
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.views.generic import DetailView, ListView

from . import mixin


class Index(ListView, mixin.TitleMixin, mixin.MetaMixin):
    template_name = "gameserver/info/index.html"
    model = models.BlogPost
    context_object_name = "posts"

    def get_ordering(self):
        return "-date_created"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["problems"] = models.Problem.objects.filter(
            is_private=False
        ).order_by("-date_created")[:5]
        context["comments"] = models.Comment.objects.order_by("-date_created")[
            :5
        ]
        moment = timezone.localtime()
        context["contests"] = models.Contest.objects.filter(
            start_time__lte=moment, end_time__gt=moment
        ).order_by("-start_time")[:5]
        return context


class BlogPost(
    DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin
):
    model = models.BlogPost
    context_object_name = "post"
    template_name = "gameserver/info/blog_post.html"
    og_type = "article"

    def get_title(self):
        return "" + self.get_object().title

    def get_author(self):
        return self.get_object().author.all()

    def get_description(self):
        return self.get_object().summary


class Editorial(
    DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin
):
    model = models.Editorial
    context_object_name = "post"
    template_name = "gameserver/info/editorial.html"
    og_type = "article"

    def get_title(self):
        return "" + self.get_object().title

    def get_author(self):
        return self.get_object().author.all()

    def get_description(self):
        return self.get_object().summary
