import logging
import traceback
import zoneinfo

from django.conf import settings
from django.contrib.redirects.middleware import RedirectFallbackMiddleware
from django.http import HttpResponseRedirect
from django.utils import timezone


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


l = logging.getLogger(__name__)


class ErrorLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if exception:
            l.error(
                f"URI: {request.build_absolute_uri()}\n"
                f"Exception: {repr(exception)}\n"
                f"{traceback.format_exc()}"
            )
