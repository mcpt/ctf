from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .. import models
from django.shortcuts import get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType
from . import mixin


class Comment(DetailView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Comment
    context_object_name = "comment"
    template_name = "gameserver/info/comment.html"

    def get_title(self):
        return "pCTF: Comment #" + str(self.get_object().pk)

    def get_description(self):
        return self.get_object().text

    def get_author(self):
        return [self.get_object().author]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment_contenttype = ContentType.objects.get_for_model(models.Comment)
        context["comments"] = models.Comment.objects.filter(
            parent_content_type=comment_contenttype,
            parent_object_id=self.get_object().pk,
        )
        return context


@require_POST
@login_required
def add_comment(request, parent_type, parent_id):
    if parent_type == "problem":
        parent = get_object_or_404(models.Problem, slug=parent_id)
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
    else:
        raise NotImplementedError
    author = request.user
    comment = models.Comment(parent=parent, text=request.POST["text"], author=author)
    comment.save()
    return redirect("comment", pk=comment.pk)
