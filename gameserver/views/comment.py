from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from .. import models
from . import mixin


class Comment(
    DetailView, mixin.TitleMixin, mixin.MetaMixin, mixin.CommentMixin
):
    model = models.Comment
    context_object_name = "comment"
    template_name = "gameserver/comment/detail.html"

    def get_title(self):
        return "Comment #" + str(self.get_object().pk)

    def get_description(self):
        return self.get_object().text

    def get_author(self):
        return [self.get_object().author]


@require_POST
@login_required
def add_comment(request, parent_type, parent_id):
    if parent_type == "problem":
        parent = get_object_or_404(models.Problem, slug=parent_id)
        if parent.is_private:
            return HttpResponseForbidden()
    elif parent_type == "user":
        parent = get_object_or_404(models.User, username=parent_id)
    elif parent_type == "solve":
        parent = get_object_or_404(models.Solve, pk=parent_id)
    elif parent_type == "comment":
        parent = get_object_or_404(models.Comment, pk=parent_id)
    elif parent_type == "post":
        parent = get_object_or_404(models.BlogPost, slug=parent_id)
    elif parent_type == "organization":
        parent = get_object_or_404(models.Organization, slug=parent_id)
    elif parent_type == "contest":
        parent = get_object_or_404(models.Contest, slug=parent_id)
        if parent.is_private:
            return HttpResponseForbidden()
    elif parent_type == "contestparticipation":
        parent = get_object_or_404(models.ContestParticipation, pk=parent_id)
    else:
        raise NotImplementedError
    author = request.user
    comment = models.Comment(
        parent=parent, text=request.POST["text"], author=author
    )
    comment.save()
    return redirect("comment", pk=comment.pk)
