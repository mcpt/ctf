from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from .. import models
from . import mixin


class Comment(DetailView, mixin.MetaMixin, mixin.CommentMixin):
    model = models.Comment
    template_name = "comment/detail.html"
    context_object_name = "comment"

    def get_title(self):
        return "Comment #" + str(self.object.pk)

    def get_description(self):
        return self.object.text

    def get_author(self):
        return [self.object.author]


@require_POST
@login_required
def add_comment(request, parent_type, parent_id):
    if parent_type == "problem":
        parent = get_object_or_404(models.Problem, slug=parent_id)
        if not parent.is_public:
            return HttpResponseForbidden()
    elif parent_type == "user":
        parent = get_object_or_404(models.User, username=parent_id)
    elif parent_type == "submission":
        parent = get_object_or_404(models.Submission, pk=parent_id)
    elif parent_type == "comment":
        parent = get_object_or_404(models.Comment, pk=parent_id)
    elif parent_type == "post":
        parent = get_object_or_404(models.BlogPost, slug=parent_id)
    elif parent_type == "organization":
        parent = get_object_or_404(models.Organization, slug=parent_id)
    elif parent_type == "contest":
        parent = get_object_or_404(models.Contest, slug=parent_id)
        if not parent.is_public:
            return HttpResponseForbidden()
    elif parent_type == "contestparticipation":
        parent = get_object_or_404(models.ContestParticipation, pk=parent_id)
    else:
        return HttpResponseBadRequest()
    author = request.user
    comment = models.Comment(parent=parent, text=request.POST["text"], author=author)
    comment.save()
    return redirect("comment", pk=comment.pk)
