from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import WalletTransaction


class PaymentSafetyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="investor@example.com", password="safe-test-password")
        self.client.force_login(self.user)

    @override_settings(MOLLIE_PAYMENTS_ENABLED=False, MOLLIE_API_KEY="")
    def test_unconfigured_mollie_cannot_create_wallet_credit(self):
        response = self.client.post(
            reverse("deposit"),
            {"amount": "100.00", "payment_method": "creditcard"},
        )

        self.assertRedirects(response, reverse("deposit_method"))
        self.assertFalse(WalletTransaction.objects.filter(user=self.user).exists())

    @override_settings(MOLLIE_PAYMENTS_ENABLED=True, MOLLIE_API_KEY="test_key")
    def test_payment_method_page_offers_card_and_bank_transfer(self):
        response = self.client.get(reverse("deposit_method"))

        self.assertContains(response, f'{reverse("deposit")}?method=creditcard')
        self.assertContains(response, f'{reverse("deposit")}?method=banktransfer')
        self.assertContains(response, "Mollie")

    @override_settings(
        MOLLIE_PAYMENTS_ENABLED=True,
        MOLLIE_API_KEY="test_key",
        MOLLIE_WEBHOOK_URL="https://lapremierbrique.com/payments/mollie/webhook/",
        MOLLIE_REDIRECT_BASE_URL="https://lapremierbrique.com",
    )
    @patch("investments.views.create_mollie_payment")
    def test_card_checkout_creates_pending_transaction_and_redirects(self, create_payment):
        create_payment.return_value = {
            "id": "tr_card",
            "status": "open",
            "_links": {"checkout": {"href": "https://www.mollie.com/checkout/card"}},
        }

        response = self.client.post(
            reverse("deposit"),
            {"amount": "100.00", "payment_method": "creditcard"},
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], "https://www.mollie.com/checkout/card")
        transaction = WalletTransaction.objects.get(user=self.user)
        self.assertEqual(transaction.amount, Decimal("100.00"))
        self.assertEqual(transaction.status, WalletTransaction.STATUS_PENDING)
        self.assertEqual(transaction.provider, "mollie-creditcard")
        self.assertEqual(transaction.reference, "tr_card")
        self.assertEqual(create_payment.call_args.kwargs["method"], "creditcard")

    @override_settings(
        MOLLIE_PAYMENTS_ENABLED=True,
        MOLLIE_API_KEY="test_key",
        MOLLIE_REDIRECT_BASE_URL="https://lapremierbrique.com",
    )
    @patch("investments.views.create_mollie_payment")
    def test_bank_transfer_checkout_uses_mollie(self, create_payment):
        create_payment.return_value = {
            "id": "tr_bank",
            "status": "open",
            "_links": {"checkout": {"href": "https://www.mollie.com/checkout/bank"}},
        }

        response = self.client.post(
            reverse("deposit"),
            {"amount": "250.00", "payment_method": "banktransfer"},
        )

        self.assertEqual(response.status_code, 303)
        transaction = WalletTransaction.objects.get(user=self.user)
        self.assertEqual(transaction.provider, "mollie-banktransfer")
        self.assertEqual(create_payment.call_args.kwargs["method"], "banktransfer")

    @override_settings(MOLLIE_API_KEY="test_key")
    @patch("investments.views.get_mollie_payment")
    def test_paid_webhook_credits_wallet_once(self, get_payment):
        transaction = WalletTransaction.objects.create(
            user=self.user,
            transaction_type=WalletTransaction.TYPE_DEPOSIT,
            status=WalletTransaction.STATUS_PENDING,
            amount=Decimal("75.00"),
            reference="tr_paid",
            provider="mollie-creditcard",
            metadata={"payment_method": "creditcard"},
        )
        get_payment.return_value = {
            "id": "tr_paid",
            "status": "paid",
            "method": "creditcard",
            "amount": {"currency": "EUR", "value": "75.00"},
            "metadata": {"transaction_id": str(transaction.pk)},
        }

        first = self.client.post(reverse("mollie_webhook"), {"id": "tr_paid"})
        second = self.client.post(reverse("mollie_webhook"), {"id": "tr_paid"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, WalletTransaction.STATUS_SUCCEEDED)
        self.assertEqual(
            WalletTransaction.objects.filter(reference="tr_paid").count(),
            1,
        )

    @override_settings(MOLLIE_API_KEY="test_key")
    @patch("investments.views.get_mollie_payment")
    def test_webhook_rejects_mismatched_amount(self, get_payment):
        transaction = WalletTransaction.objects.create(
            user=self.user,
            transaction_type=WalletTransaction.TYPE_DEPOSIT,
            status=WalletTransaction.STATUS_PENDING,
            amount=Decimal("75.00"),
            reference="tr_wrong_amount",
            provider="mollie-banktransfer",
        )
        get_payment.return_value = {
            "id": "tr_wrong_amount",
            "status": "paid",
            "amount": {"currency": "EUR", "value": "750.00"},
            "metadata": {"transaction_id": str(transaction.pk)},
        }

        response = self.client.post(reverse("mollie_webhook"), {"id": "tr_wrong_amount"})

        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, WalletTransaction.STATUS_PENDING)

    def test_legacy_bank_transfer_url_redirects_to_mollie_checkout_form(self):
        response = self.client.get(reverse("bank_transfer"))

        self.assertRedirects(
            response,
            f'{reverse("deposit")}?method=banktransfer',
            fetch_redirect_response=False,
        )


class GoogleLoginLinkTests(TestCase):
    def test_login_page_posts_to_google_oauth_start(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, f'action="{reverse("social:begin", args=["google-oauth2"])}"')
        self.assertContains(response, 'method="post"')

    def test_signup_page_posts_to_google_oauth_start(self):
        response = self.client.get("/signup.html")

        self.assertContains(response, f'action="{reverse("social:begin", args=["google-oauth2"])}"')
        self.assertContains(response, 'method="post"')

    @override_settings(
        SOCIAL_AUTH_REQUIRE_POST=True,
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY="test-client.apps.googleusercontent.com",
        SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET="test-secret",
    )
    def test_google_oauth_start_accepts_post_and_redirects_to_google(self):
        response = self.client.post(reverse("social:begin", args=["google-oauth2"]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://accounts.google.com/"))


class SearchIndexingTests(TestCase):
    @override_settings(SITE_URL="https://lapremierbrique.com")
    def test_robots_points_to_canonical_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sitemap: https://lapremierbrique.com/sitemap.xml")

    @override_settings(SITE_URL="https://lapremierbrique.com")
    def test_sitemap_contains_homepage(self):
        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertContains(response, "<loc>https://lapremierbrique.com/</loc>")

    @override_settings(SITE_URL="https://new.example")
    def test_homepage_canonical_uses_configured_site_url(self):
        response = self.client.get("/")

        self.assertContains(response, 'rel="canonical" href="https://new.example/"')

    def test_homepage_uses_same_domain_favicon(self):
        response = self.client.get("/")

        self.assertContains(response, 'href="/css/favicon.svg"')

    def test_favicon_is_publicly_served_as_svg(self):
        response = self.client.get("/css/favicon.svg")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")


class PublicNavbarTests(TestCase):
    def test_anonymous_homepage_has_original_login_action(self):
        response = self.client.get("/")

        self.assertContains(response, 'href="/login.html"', count=1)
        self.assertNotContains(response, "navbar_mobile_auth")

    def test_authenticated_homepage_replaces_login_with_account(self):
        user = User.objects.create_user(username="navbar@example.com", password="safe-test-password")
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, "navbar_account_btn")
        self.assertNotContains(response, "navbar_mobile_auth")
        self.assertNotContains(response, 'class="button_text style-12">Connexion</div>')

# Create your tests here.
