import re

from django import template
from django.http import QueryDict
from django.shortcuts import resolve_url

register = template.Library()


@register.filter
def get_search_page(request):
    if request.path in ["/users/", "/users"]:
        return resolve_url("user_list")
    elif match := re.fullmatch(r"^/contest/([^/]+)/scoreboard/organization/([^/]+$)", request.path):
        return resolve_url(
            "contest_organization_scoreboard", contest_slug=match.group(1), org_slug=match.group(2)
        )
    elif match := re.fullmatch(r"^/contest/([^/]+)/scoreboard$", request.path):
        return resolve_url("contest_scoreboard", slug=match.group(1))
    return


@register.filter
def format_GET(GET: QueryDict):
    GET = GET.copy()
    GET.pop("page", None)
    if GET.get("nfts", None) == "":
        del GET["nfts"]
    return GET.urlencode()
