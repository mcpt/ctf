from django.db import models
from .profile import User
from django.urls import reverse

# Create your models here.


class BlogPost(models.Model):
    author = models.ManyToManyField(User, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=128, blank=True)
    text = models.TextField(blank=True)
    summary = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_post', args=[self.pk])
