from allauth.socialaccount.providers import OpenIDProvider


class KyiiProvider(OpenIDProvider):
    id = "kyii"
    name = "Kyii"

provider_classes = [KyiiProvider]
