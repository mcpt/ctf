from enum import Enum
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .problem import Problem
from .profile import User

# Create your models here.


class Post(models.Model):
    author = models.ManyToManyField(User, blank=True)

    title = models.CharField(max_length=128, blank=True)
    slug = models.SlugField(unique=True)
    text = models.TextField(blank=True)
    summary = models.CharField(max_length=150)

    date_created = models.DateTimeField(auto_now_add=True)
    date_last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class BlogPost(Post):
    def get_absolute_url(self):
        return reverse("blog_post", args=[self.slug])


class Writeup(Post):
    class Pointee(Enum):
        POST = _("Post")
        URL = _("External URL")

    problem = models.ForeignKey(Problem, related_name="writeups", on_delete=models.CASCADE)
    url = models.URLField(null=True, blank=True)

    def get_absolute_url(self):
        return self.url if self.url else reverse("writeup", args=[self.slug])

    def __str__(self):
        return f'By {self.author}'

    @property
    def get_absolute_model_url(self):
        return reverse("writeup", args=[self.slug])
