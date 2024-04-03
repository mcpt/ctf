from typing import Iterable
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone

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
    date_edited = models.DateTimeField(auto_now_add=True)

    def save(
        self,
        force_insert: bool = ...,
        force_update: bool = ...,
        using: str | None = ...,
        update_fields: Iterable[str] | None = ...,
    ) -> None:
        self.date_edited = timezone.now()
        return super().save(force_insert, force_update, using, update_fields)

    @property
    def edited(self):
        return self.date_created != self.date_edited

    def __str__(self):
        return f"Re: {self.parent}"

    def get_absolute_url(self):
        return reverse("comment", args=[self.pk])
