from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from .profile import User

# Create your models here.


class Comment(models.Model):
    parent_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent_object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("parent_content_type", "parent_object_id")
    comments = GenericRelation(
        "Comment",
        content_type_field="parent_content_type",
        object_id_field="parent_object_id",
    )

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    text = models.TextField()

    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(
        auto_now=True,
    )

    @property
    def edited(self):
        return self.date_created != self.date_edited

    def __str__(self):
        return f"Re: {self.parent}"

    def get_absolute_url(self):
        return reverse("comment", args=[self.pk])
