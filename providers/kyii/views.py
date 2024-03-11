import urllib.parse

import requests
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

from .provider import KyiiProvider


class KyiiOAuth2Adapter(OAuth2Adapter):
    provider_id = KyiiProvider.id

    @property
    def _base_url(self) -> str:
        return self.get_provider().get_settings().get("BASE_URL")

    @property
    def access_token_url(self) -> str:
        return urllib.parse.urljoin(self._base_url, "./oauth/token/")

    @property
    def authorize_url(self) -> str:
        return urllib.parse.urljoin(self._base_url, "./oauth/authorize/")

    @property
    def profile_url(self) -> str:
        return urllib.parse.urljoin(self._base_url, "./oauth/userinfo/")

    def complete_login(self, request, app, token, **kwargs):
        resp = requests.get(
            self.profile_url,
            headers={
                "Authorization": f"Bearer {token.token}",
            },
        )
        resp.raise_for_status()
        extra_data = resp.json()
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login


oauth2_login = OAuth2LoginView.adapter_view(KyiiOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(KyiiOAuth2Adapter)
