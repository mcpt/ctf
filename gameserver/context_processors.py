from django.conf import settings


def settings_context(request):
    return {
        "GOOGLE_ANALYTICS_ON_ALL_VIEWS": settings.GOOGLE_ANALYTICS_ON_ALL_VIEWS,
        "GOOGLE_ANALYTICS_TRACKING_ID": settings.GOOGLE_ANALYTICS_TRACKING_ID,
        "TOS_URL": settings.TOS_URL,
        "NAVBAR": settings.NAVBAR,
        "SCHEME": settings.SCHEME,
        "KEYWORDS": settings.KEYWORDS,
    }
