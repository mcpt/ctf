from django.conf import settings


def settings_context(request):
    return {
        "TOS_URL": settings.TOS_URL,
        "NAVBAR": settings.NAVBAR,
        "SCHEME": settings.SCHEME,
        "KEYWORDS": settings.KEYWORDS,
    }
