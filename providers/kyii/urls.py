from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from .provider import KyiiProvider

urlpatterns = default_urlpatterns(KyiiProvider)
