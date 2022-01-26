import zoneinfo
from django.conf import settings
from django.utils import timezone
from django.contrib.redirects.middleware import RedirectFallbackMiddleware
from django.http import HttpResponseRedirect


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            timezone.activate(zoneinfo.ZoneInfo(request.user.timezone))
        else:
            timezone.activate(zoneinfo.ZoneInfo(settings.DEFAULT_TIMEZONE))
        return self.get_response(request)


class ContestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.update_contest()
            request.participation = request.user.current_contest
            request.in_contest = request.participation is not None
        else:
            request.in_contest = False
            request.participation = None
        return self.get_response(request)

class RedirectFallbackTemporaryMiddleware(RedirectFallbackMiddleware):
    response_redirect_class = HttpResponseRedirect
