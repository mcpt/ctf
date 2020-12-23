from django.views.generic import DetailView, ListView
from .. import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import UserPassesTestMixin
from . import mixin


class SolveList(ListView, mixin.TitleMixin, mixin.MetaMixin):
    model = models.Solve
    context_object_name = "solves"
    template_name = "gameserver/solve/list.html"
    paginate_by = 50
    title = "pCTF: Solves"

    def get_ordering(self):
        return "-created"
