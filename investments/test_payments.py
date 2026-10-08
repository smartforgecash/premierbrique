import json
from decimal import Decimal
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth.models import User
from django.test import Client, TestCase, SimpleTestCase, override_settings
from django.urls import reverse

from .models import WalletTransaction
from .payments import attempt_token, confirm_bank_transfer, safe_checkout_url
from .services import wallet_balance
from .sumup import SumUpAPIError, create_checkout, get_checkout


@override_settings(
    CARD_PAYMENTS_ENABLED=True,
    SUMUP_API_KEY="test-key",
    SUMUP_MERCHANT_CODE="MTEST",
    SITE_URL="https://la-premiere-brique.com",
    BANK_TRANSFER_ACCOUNT_HOLDER="Test Merchant",
    BANK_TRANSFER_IBAN="GB82WEST12345698765432",
    BANK_TRANSFER_BIC="TESTGB2LXXX",
    BANK_TRANSFER_BANK_NAME="Test Bank",
)
class SumUpPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="investor@example.com", password="test-password")
        self.client.force_login(self.user)

    def pending(self, reference="checkout-1"):
        return WalletTransaction.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("75.00"),
            status="pending", provider="sumup-card", reference=reference,
            metadata={"checkout_reference": "PB-reference", "merchant_code": "MTEST"},
        )

    def checkout(self, transaction, **overrides):
        return {
            "id": transaction.reference or "checkout-1",
            "checkout_reference": transaction.metadata["checkout_reference"],
            "merchant_code": "MTEST", "amount": 75, "currency": "EUR", "status": "PAID",
            **overrides,
        }

    def webhook(self, transaction, checkout_id=None, client=None):
        return (client or self.client).post(
            reverse("sumup_webhook") + f"?transaction_id={transaction.pk}",
            data={"event_type": "CHECKOUT_STATUS_CHANGED", "id": checkout_id or transaction.reference},
            content_type="application/json",
        )

    def card_post(self, token=None, amount="100.00"):
        return self.client.post(reverse("deposit"), {
            "amount": amount, "payment_method": "creditcard",
            "payment_token": token or attempt_token(self.user, "creditcard"),
        })

    def bank_post(self, token=None, amount="250.00"):
        return self.client.post(reverse("bank_transfer"), {
            "amount": amount, "payment_token": token or attempt_token(self.user, "banktransfer"),
        })

    def test_methods_offer_sumup_and_manual_bank_without_mollie(self):
        response = self.client.get(reverse("deposit_method"))
        self.assertContains(response, reverse("bank_transfer"))
        self.assertContains(response, "SumUp")
        self.assertNotContains(response, "Mollie")
        self.assertNotContains(response, 'aria-disabled="true"')

    @override_settings(SUMUP_API_KEY="")
    def test_missing_key_blocks_card_but_not_bank(self):
        response = self.card_post()
        self.assertRedirects(response, reverse("deposit_method"))
        self.assertFalse(WalletTransaction.objects.exists())
        self.assertEqual(self.bank_post().status_code, 302)

    @override_settings(CARD_PAYMENTS_ENABLED=False)
    def test_explicit_card_disable_is_respected(self):
        self.assertRedirects(self.card_post(), reverse("deposit_method"))
        self.assertFalse(WalletTransaction.objects.exists())

    @patch("investments.payments.create_checkout")
    def test_card_creation_is_pending_and_duplicate_submit_reuses_checkout(self, create):
        def result(*args, **kwargs):
            return {
                "id": "checkout-new", "amount": 100, "currency": "EUR", "merchant_code": "MTEST",
                "checkout_reference": kwargs["reference"], "status": "PENDING",
                "hosted_checkout_url": "https://checkout.sumup.com/pay/new",
            }
        create.side_effect = result
        token = attempt_token(self.user, "creditcard")
        for _ in range(2):
            response = self.card_post(token)
            self.assertEqual(response.status_code, 303)
            self.assertEqual(response["Location"], "https://checkout.sumup.com/pay/new")
        create.assert_called_once()
        transaction = WalletTransaction.objects.get()
        self.assertEqual(transaction.status, "pending")
        self.assertEqual(transaction.reference, "checkout-new")
        self.assertEqual(wallet_balance(self.user), Decimal("0"))
        self.assertEqual(create.call_args.kwargs["webhook_url"],
                         f"https://la-premiere-brique.com/payments/sumup/webhook/?transaction_id={transaction.pk}")

    @patch("investments.payments.create_checkout", side_effect=SumUpAPIError("timeout"))
    def test_creation_timeout_does_not_credit_or_retry_same_token(self, create):
        token = attempt_token(self.user, "creditcard")
        self.card_post(token)
        self.card_post(token)
        self.assertEqual(wallet_balance(self.user), 0)
        self.assertEqual(WalletTransaction.objects.count(), 1)
        create.assert_called_once()

    @patch("investments.payments.create_checkout")
    def test_provider_mismatch_or_unsafe_redirect_cannot_credit(self, create):
        create.return_value = {"id": "fake", "hosted_checkout_url": "https://attacker.example/"}
        self.card_post()
        self.assertEqual(wallet_balance(self.user), 0)

    def test_forged_or_other_users_form_cannot_create_deposit(self):
        other = User.objects.create_user(username="other")
        for token in ["forged", attempt_token(other, "creditcard"), attempt_token(self.user, "banktransfer")]:
            self.assertEqual(self.card_post(token).status_code, 200)
        self.assertFalse(WalletTransaction.objects.exists())

    def test_invalid_amounts_cannot_create_deposit(self):
        for amount in ["NaN", "Infinity", "-1", "0", "2000.01", "1.001", "100000000000000"]:
            self.card_post(amount=amount)
        self.assertFalse(WalletTransaction.objects.exists())

    @patch("investments.payments.get_checkout")
    def test_webhook_credits_once_and_ignores_late_failure(self, get):
        transaction = self.pending()
        get.return_value = self.checkout(transaction)
        public = Client(enforce_csrf_checks=True)
        self.assertEqual(self.webhook(transaction, client=public).status_code, 204)
        self.assertEqual(self.webhook(transaction, client=public).status_code, 204)
        get.return_value = self.checkout(transaction, status="FAILED")
        self.webhook(transaction)
        self.assertEqual(wallet_balance(self.user), Decimal("75"))
        self.assertEqual(WalletTransaction.objects.count(), 1)

    @patch("investments.payments.get_checkout")
    def test_webhook_rejects_mismatched_amount_currency_merchant_reference_or_id(self, get):
        transaction = self.pending()
        for overrides in [
            {"amount": 750}, {"currency": "USD"}, {"merchant_code": "OTHER"},
            {"checkout_reference": "someone-else"}, {"id": "someone-else"}, {"amount": "NaN"},
        ]:
            get.return_value = self.checkout(transaction, **overrides)
            self.assertEqual(self.webhook(transaction).status_code, 400)
            self.assertEqual(wallet_balance(self.user), 0)

    @patch("investments.payments.get_checkout")
    def test_early_webhook_can_bind_verified_checkout(self, get):
        transaction = self.pending(reference="")
        get.return_value = self.checkout(transaction)
        self.assertEqual(self.webhook(transaction, checkout_id="checkout-1").status_code, 204)
        transaction.refresh_from_db()
        self.assertEqual(transaction.reference, "checkout-1")
        self.assertEqual(wallet_balance(self.user), 75)

    @patch("investments.payments.get_checkout", side_effect=SumUpAPIError("unavailable"))
    def test_verification_failure_requests_retry_without_credit(self, get):
        transaction = self.pending()
        self.assertEqual(self.webhook(transaction).status_code, 503)
        self.assertEqual(wallet_balance(self.user), 0)

    @patch("investments.payments.get_checkout")
    def test_failed_or_unpaid_checkout_never_credits_wallet(self, get):
        transaction = self.pending()
        for status in ["PENDING", "FAILED", "EXPIRED"]:
            get.return_value = self.checkout(transaction, status=status)
            self.webhook(transaction)
            self.assertEqual(wallet_balance(self.user), 0)

    def test_webhook_rejects_bad_json_and_ignores_unknown_events(self):
        url = reverse("sumup_webhook")
        self.assertEqual(self.client.post(url, data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post(url, data="[]", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post(url, data={"event_type": "FUTURE"}, content_type="application/json").status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 405)

    @patch("investments.payments.get_checkout")
    def test_return_verifies_payment_instead_of_trusting_query_status(self, get):
        transaction = self.pending()
        get.return_value = self.checkout(transaction, status="PENDING")
        url = reverse("sumup_return") + f"?transaction_id={transaction.pk}&status=PAID"
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(wallet_balance(self.user), 0)
        get.return_value = self.checkout(transaction)
        self.client.get(url)
        self.assertEqual(wallet_balance(self.user), 75)

    @patch("investments.payments.get_checkout")
    def test_return_cannot_access_another_users_deposit(self, get):
        transaction = self.pending()
        self.client.force_login(User.objects.create_user(username="other"))
        self.assertEqual(self.client.get(reverse("sumup_return") + f"?transaction_id={transaction.pk}").status_code, 404)
        get.assert_not_called()

    def test_bank_details_reference_and_pending_balance(self):
        response = self.bank_post()
        transaction = WalletTransaction.objects.get()
        self.assertEqual(transaction.status, "pending")
        self.assertEqual(transaction.provider, "manual-bank-transfer")
        self.assertEqual(wallet_balance(self.user), 0)
        response = self.client.get(response["Location"])
        for value in ["Test Merchant", "GB82WEST12345698765432", "TESTGB2LXXX", "Test Bank", transaction.reference]:
            self.assertContains(response, value)
        self.assertNotContains(response, "Stripe")
        self.assertNotContains(response, "Mollie")

    def test_bank_repeated_submission_does_not_duplicate(self):
        token = attempt_token(self.user, "banktransfer")
        self.bank_post(token)
        self.bank_post(token)
        self.assertEqual(WalletTransaction.objects.count(), 1)
        self.bank_post(token, amount="500")
        self.assertEqual(WalletTransaction.objects.count(), 1)
        self.assertEqual(WalletTransaction.objects.get().amount, 250)

    @override_settings(BANK_TRANSFER_IBAN="")
    def test_missing_bank_details_blocks_deposit(self):
        self.bank_post()
        self.assertFalse(WalletTransaction.objects.exists())

    def test_bank_details_cannot_be_accessed_by_another_user(self):
        url = self.bank_post()["Location"]
        self.client.force_login(User.objects.create_user(username="other"))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_manual_confirmation_credits_once_and_records_admin(self):
        self.bank_post()
        transaction = WalletTransaction.objects.get()
        staff = User.objects.create_superuser(username="admin", password="test-password")
        self.assertTrue(confirm_bank_transfer(transaction.pk, staff))
        self.assertFalse(confirm_bank_transfer(transaction.pk, staff))
        self.assertEqual(wallet_balance(self.user), 250)
        transaction.refresh_from_db()
        self.assertEqual(transaction.metadata["confirmed_by"], staff.pk)
        self.assertTrue(transaction.metadata["confirmed_at"])
        self.assertFalse(confirm_bank_transfer(self.pending().pk, staff))

    def test_customer_cannot_use_admin_to_credit_themselves(self):
        response = self.client.post("/admin/investments/wallettransaction/", {
            "action": "confirm_received_transfers", "_selected_action": "1",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_csrf_required_for_card_and_bank_forms(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("deposit"), {"amount": 50}).status_code, 403)
        self.assertEqual(client.post(reverse("bank_transfer"), {"amount": 50}).status_code, 403)

    def test_old_bank_link_redirects_to_manual_transfer(self):
        self.assertRedirects(self.client.get(reverse("deposit") + "?method=banktransfer"), reverse("bank_transfer"))

    def test_invalid_return_id_does_not_cause_server_error(self):
        self.assertEqual(self.client.get(reverse("sumup_return") + "?transaction_id=bad").status_code, 400)

    def test_anonymous_customer_must_login(self):
        self.client.logout()
        for name in ["deposit", "deposit_method", "bank_transfer", "sumup_return"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)


class SumUpClientTests(SimpleTestCase):
    def test_invalid_or_untrusted_checkout_links_are_rejected(self):
        for url in ["https://[broken", "http://checkout.sumup.com/pay/1", "https://checkout.sumup.com.evil.example/", "https://name:password@checkout.sumup.com/", None]:
            self.assertFalse(safe_checkout_url(url))

    @patch("investments.sumup.urlopen")
    def test_request_has_auth_exact_amount_and_distinct_return_and_webhook(self, open_url):
        open_url.return_value.__enter__.return_value.read.return_value = b'{"id":"checkout"}'
        create_checkout("secret-test-key", merchant_code="MTEST", amount=Decimal("19.99"),
                        reference="PB-test", redirect_url="https://example.com/return/",
                        webhook_url="https://example.com/webhook/")
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.sumup.com/v0.1/checkouts")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-test-key")
        body = json.loads(request.data)
        self.assertEqual(body["amount"], 19.99)
        self.assertEqual(body["currency"], "EUR")
        self.assertEqual(body["return_url"], "https://example.com/webhook/")
        self.assertEqual(body["redirect_url"], "https://example.com/return/")
        self.assertEqual(body["hosted_checkout"], {"enabled": True})

    @patch("investments.sumup.urlopen", side_effect=URLError("network"))
    def test_network_failure_is_controlled(self, open_url):
        with self.assertRaises(SumUpAPIError):
            get_checkout("secret", "id")

    @patch("investments.sumup.urlopen")
    def test_malformed_response_is_controlled(self, open_url):
        for body in [b'[]', b'not-json']:
            open_url.return_value.__enter__.return_value.read.return_value = body
            with self.assertRaises(SumUpAPIError):
                get_checkout("secret", "id")
