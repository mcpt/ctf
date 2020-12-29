from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
