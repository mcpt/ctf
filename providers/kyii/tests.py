# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from importlib import import_module

from allauth.account import app_settings as account_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.signals import user_signed_up
from allauth.tests import MockedResponse, TestCase, patch
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from requests.exceptions import HTTPError

from .models import SocialAccount, SocialToken
from .provider import KyiiProvider
from .tests import OAuth2TestsMixin


@override_settings(
    SOCIALACCOUNT_AUTO_SIGNUP=True,
    ACCOUNT_SIGNUP_FORM_CLASS=None,
    ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.MANDATORY,
)
class KyiiTests(OAuth2TestsMixin, TestCase):
    provider_id = KyiiProvider.id

    def get_mocked_response(
        self,
        family_name="First",
        given_name="Last",
        name="First Last",
        email="first.last@example.com",
        verified_email=True,
    ):
        return MockedResponse(
            200,
            f"""
              {"family_name": "%s", "name": "%s",
               "picture": "https://lh5.googleusercontent.com/photo.jpg",
               "locale": "nl", "gender": "male",
               "email": "%s",
               "link": "https://plus.google.com/108204268033311374519",
               "given_name": "%s", "id": "108204268033311374519",
               "verified_email": %s }
        """
            % (
                family_name,
                name,
                email,
                given_name,
                (repr(verified_email).lower()),
            ),
        )

    def test_kyii_compelete_login_401(self):
        from .providers.kyii.views import KyiiOAuth2Adapter

        class LessMockedResponse(MockedResponse):
            def raise_for_status(self):
                if self.status_code != 200:
                    raise HTTPError(None)

        request = RequestFactory().get(reverse(self.provider.id + "_login"), dict(process="login"))

        adapter = KyiiOAuth2Adapter(request)
        app = adapter.get_provider().get_app(request)
        token = SocialToken(token="some_token")
        response_with_401 = LessMockedResponse(
            401,
            """
            {"error": {
              "errors": [{
                "domain": "global",
                "reason": "authError",
                "message": "Invalid Credentials",
                "locationType": "header",
                "location": "Authorization" } ],
              "code": 401,
              "message": "Invalid Credentials" }
            }""",
        )
        with patch(".providers.kyii.views.requests") as patched_requests:
            patched_requests.get.return_value = response_with_401
            with self.assertRaises(HTTPError):
                adapter.complete_login(request, app, token)

    def test_username_based_on_email(self):
        first_name = "明"
        last_name = "小"
        email = "raymond.penners@example.com"
        self.login(
            self.get_mocked_response(
                name=first_name + " " + last_name,
                email=email,
                given_name=first_name,
                family_name=last_name,
                verified_email=True,
            )
        )
        user = User.objects.get(email=email)
        self.assertEqual(user.username, "raymond.penners")

    def test_email_verified(self):
        test_email = "raymond.penners@example.com"
        self.login(self.get_mocked_response(verified_email=True))
        email_address = EmailAddress.objects.get(email=test_email, verified=True)
        self.assertFalse(EmailConfirmation.objects.filter(email_address__email=test_email).exists())
        account = email_address.user.socialaccount_set.all()[0]
        self.assertEqual(account.extra_data["given_name"], "Raymond")

    def test_user_signed_up_signal(self):
        sent_signals = []

        def on_signed_up(sender, request, user, **kwargs):
            sociallogin = kwargs["sociallogin"]
            self.assertEqual(sociallogin.account.provider, KyiiProvider.id)
            self.assertEqual(sociallogin.account.user, user)
            sent_signals.append(sender)

        user_signed_up.connect(on_signed_up)
        self.login(self.get_mocked_response(verified_email=True))
        self.assertTrue(len(sent_signals) > 0)

    @override_settings(ACCOUNT_EMAIL_CONFIRMATION_HMAC=False)
    def test_email_unverified(self):
        test_email = "raymond.penners@example.com"
        resp = self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects.get(email=test_email)
        self.assertFalse(email_address.verified)
        self.assertTrue(EmailConfirmation.objects.filter(email_address__email=test_email).exists())
        self.assertTemplateUsed(resp, "account/email/email_confirmation_signup_subject.txt")

    def test_email_verified_stashed(self):
        # http://slacy.com/blog/2012/01/how-to-set-session-variables-in-django-unit-tests/
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        request = RequestFactory().get("/")
        request.session = self.client.session
        adapter = get_adapter(request)
        test_email = "raymond.penners@example.com"
        adapter.stash_verified_email(request, test_email)
        request.session.save()

        self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects.get(email=test_email)
        self.assertTrue(email_address.verified)
        self.assertFalse(EmailConfirmation.objects.filter(email_address__email=test_email).exists())

    def test_account_connect(self):
        email = "user@example.com"
        user = User.objects.create(username="user", is_active=True, email=email)
        user.set_password("test")
        user.save()
        EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
        self.client.login(username=user.username, password="test")
        self.login(self.get_mocked_response(verified_email=True), process="connect")
        # Check if we connected...
        self.assertTrue(SocialAccount.objects.filter(user=user, provider=KyiiProvider.id).exists())
        # For now, we do not pick up any new e-mail addresses on connect
        self.assertEqual(EmailAddress.objects.filter(user=user).count(), 1)
        self.assertEqual(EmailAddress.objects.filter(user=user, email=email).count(), 1)

    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.MANDATORY,
        SOCIALACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.NONE,
    )
    def test_social_email_verification_skipped(self):
        test_email = "raymond.penners@example.com"
        self.login(self.get_mocked_response(verified_email=False))
        email_address = EmailAddress.objects.get(email=test_email)
        self.assertFalse(email_address.verified)
        self.assertFalse(EmailConfirmation.objects.filter(email_address__email=test_email).exists())

    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.OPTIONAL,
        SOCIALACCOUNT_EMAIL_VERIFICATION=account_settings.EmailVerificationMethod.OPTIONAL,
    )
    def test_social_email_verification_optional(self):
        self.login(self.get_mocked_response(verified_email=False))
        self.assertEqual(len(mail.outbox), 1)
        self.login(self.get_mocked_response(verified_email=False))
        self.assertEqual(len(mail.outbox), 1)


@override_settings(
    SOCIALACCOUNT_PROVIDERS={
        "kyii": {
            "APP": {
                "client_id": "app123id",
                "key": "kyii",
                "secret": "dummy",
            }
        }
    }
)
class AppInSettingsTests(KyiiTests):
    """
    Run the same set of tests but without having a SocialApp entry.
    """

    pass
