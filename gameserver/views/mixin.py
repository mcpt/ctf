import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.views.generic.base import ContextMixin

from .. import models

User = get_user_model()


class MetaMixin(ContextMixin):
    og_type = "website"
    title = ""
    description = settings.DESCRIPTION
    og_image = None

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def get_og_image(self):
        return self.og_image

    def get_author(self):
        return models.User.objects.none()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        context["site"] = Site.objects.get_current()

        context["og_type"] = self.og_type

        context["page_title"] = "mCTF"
        title = self.get_title()
        if title != "":
            context["title"] = title
            context["page_title"] = f"{title} - mCTF"

        description = self.get_description()
        description = description.strip(" ").replace("\n", " ")
        description = description[: min(150, len(description))]
        if description == "":
            description = settings.DESCRIPTION
        context["meta_description"] = description

        # TODO: Authors

        context["og_image"] = self.get_og_image()

        return context


class CommentMixin(ContextMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        contenttype = ContentType.objects.get_for_model(self.model)
        context["comments"] = models.Comment.objects.filter(
            parent_content_type=contenttype,
            parent_object_id=self.object.pk,
        )
        return context
