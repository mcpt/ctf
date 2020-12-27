import pytz
from django.utils import timezone
from pCTF import settings


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            timezone.activate(pytz.timezone(request.user.timezone))
        else:
            timezone.activate(pytz.timezone(settings.DEFAULT_TIMEZONE))
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
