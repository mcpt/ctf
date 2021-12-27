from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .problem import Problem
from .profile import User

# Create your models here.


class Post(models.Model):
    author = models.ManyToManyField(User, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_last_modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=128, blank=True)
    text = models.TextField(blank=True)
    summary = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True


class BlogPost(Post):
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_post", args=[self.slug])


class Writeup(Post):
    class Pointee(models.TextChoices):
        POST = "P", _("Post")
        URL = "E", _("External URL")

    target = models.ForeignKey(Problem, related_name="writeups", on_delete=models.CASCADE)
    url = models.URLField(null=True, blank=True)
    pointee = models.CharField(max_length=1, choices=Pointee.choices, default=Pointee.URL)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return self.url if self.pointee == "E" else reverse("writeup", args=[self.slug])

    def get_absolute_model_url(self):
        return reverse("writeup", args=[self.slug])
