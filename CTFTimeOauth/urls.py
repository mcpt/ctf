from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import CTFTimeOauth2AProvider


urlpatterns = default_urlpatterns(CTFTimeOauth2AProvider)