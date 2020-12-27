from django.views.generic import DetailView, ListView
from .. import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import UserPassesTestMixin
from . import mixin
from django.shortcuts import redirect


class SolveList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Solve
    context_object_name = "solves"
    template_name = "gameserver/solve/list.html"
    paginate_by = 50
    title = "pCTF: Solves"

    def get_ordering(self):
        return "-created"

    def get(self, request, *args, **kwargs):
        if request.in_contest:
            return redirect('contest_solves', slug=request.participation.contest.slug)
        else:
            return super().get(request, *args, **kwargs)
