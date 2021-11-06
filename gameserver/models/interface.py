from django.db import models
from django.urls import reverse

from .profile import User

# Create your models here.


class BlogPost(models.Model):
    author = models.ManyToManyField(User, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_last_modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=128, blank=True)
    text = models.TextField(blank=True)
    summary = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_post", args=[self.slug])
