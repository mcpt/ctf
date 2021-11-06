from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView

from .. import models
from . import mixin


class SolveList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    context_object_name = "solves"
    template_name = "gameserver/solve/list.html"
    paginate_by = 50
    title = "Solves"

    def get_queryset(self):
        queryset = models.Solve.objects.order_by("-created")
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(problem__is_private=False) | Q(solver=self.request.user)
            )
        else:
            queryset = queryset.filter(problem__is_private=False)
        return queryset

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect(
                "contest_solves", slug=request.participation.contest.slug
            )
        else:
            return super().get(request, *args, **kwargs)
