from allauth.account.models import EmailAddress
from allauth.socialaccount.app_settings import QUERY_EMAIL
from allauth.socialaccount.providers.base import AuthAction, ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


SCOPE_OPENID = 'openid'
SCOPE_EMAIL = 'email'
SCOPE_PROFILE = 'profile'


class KyiiAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get("link")

    def get_avatar_url(self):
        return self.account.extra_data.get("picture")

    def to_str(self):
        dflt = super(KyiiAccount, self).to_str()
        return self.account.extra_data.get("name", dflt)


class KyiiProvider(OAuth2Provider):
    id = "kyii"
    name = "Kyii"
    account_class = KyiiAccount

    def get_default_scope(self):
        scope = [SCOPE_OPENID, SCOPE_PROFILE]
        if QUERY_EMAIL:
            scope.append(SCOPE_EMAIL)
        return scope

    def extract_uid(self, data):
        return str(data["sub"])

    def extract_common_fields(self, data):
        return dict(
            email=data.get("email"),
            last_name=data.get("family_name"),
            first_name=data.get("given_name"),
        )

    def extract_email_addresses(self, data):
        ret = []
        email = data.get("email")
        if email and data.get("verified_email"):
            ret.append(EmailAddress(email=email, verified=True, primary=True))
        return ret


provider_classes = [KyiiProvider]
