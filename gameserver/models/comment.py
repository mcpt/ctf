from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from .profile import User
from django.urls import reverse

# Create your models here.


class Comment(models.Model):
    parent_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    parent_object_id = models.PositiveIntegerField()
    parent = GenericForeignKey("parent_content_type", "parent_object_id")
    comments = GenericRelation('Comment', content_type_field='parent_content_type', object_id_field='parent_object_id')

    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    text = models.TextField()

    def get_absolute_url(self):
        return reverse('comment', args=[self.pk])
