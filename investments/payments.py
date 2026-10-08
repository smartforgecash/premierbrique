"""SumUp card deposits and manually reconciled SEPA transfers."""
import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction as db_transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import DepositForm
from .models import WalletTransaction
from .services import wallet_balance
from .sumup import SumUpAPIError, create_checkout, get_checkout

logger = logging.getLogger(__name__)
CARD_PROVIDER = "sumup-card"
BANK_PROVIDER = "manual-bank-transfer"
TOKEN_SALT = "deposit-attempt"


def cards_available():
    return bool(settings.CARD_PAYMENTS_ENABLED and settings.SUMUP_API_KEY and settings.SUMUP_MERCHANT_CODE)


def bank_details():
    return {
        "account_holder": settings.BANK_TRANSFER_ACCOUNT_HOLDER.strip(),
        "iban": settings.BANK_TRANSFER_IBAN.replace(" ", "").strip().upper(),
        "bic": settings.BANK_TRANSFER_BIC.strip().upper(),
        "bank_name": settings.BANK_TRANSFER_BANK_NAME.strip(),
    }


def public_url(request, name, transaction_id):
    base = settings.SITE_URL.rstrip("/")
    path = reverse(name)
    url = f"{base}{path}" if base else request.build_absolute_uri(path)
    return f"{url}?transaction_id={transaction_id}"


def attempt_token(user, method):
    return signing.dumps([user.pk, method, uuid4().hex], salt=TOKEN_SALT)


def reserve_transaction(request, form, method):
    try:
        user_id, token_method, reference = signing.loads(
            request.POST.get("payment_token", ""), salt=TOKEN_SALT, max_age=86400,
        )
        if user_id != request.user.pk or token_method != method or not isinstance(reference, str) or len(reference) != 32:
            raise ValueError("Invalid payment token")
    except (signing.BadSignature, ValueError, TypeError):
        raise ValueError("Le formulaire a expiré. Rechargez la page.")
    provider = CARD_PROVIDER if method == "creditcard" else BANK_PROVIDER
    # Serialize submissions for this user, including two simultaneous clicks.
    with db_transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        existing = WalletTransaction.objects.filter(
            user=request.user, provider=provider, metadata__attempt=reference,
        ).first()
        if existing:
            if existing.amount != form.cleaned_data["amount"]:
                raise ValueError("Ce formulaire a déjà été utilisé. Rechargez la page.")
            return existing, False
        transaction = WalletTransaction.objects.create(
            user=request.user,
            transaction_type=WalletTransaction.TYPE_DEPOSIT,
            amount=form.cleaned_data["amount"],
            status=WalletTransaction.STATUS_PENDING,
            provider=provider,
            reference=f"PB-{reference.upper()}" if method == "banktransfer" else "",
            metadata={
                "attempt": reference,
                "checkout_reference": f"PB-{reference}",
                "merchant_code": settings.SUMUP_MERCHANT_CODE if method == "creditcard" else "",
                "bank_details": bank_details() if method == "banktransfer" else {},
            },
        )
    return transaction, True


def safe_checkout_url(url):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and parsed.hostname == "checkout.sumup.com" and not parsed.username and not parsed.password


def sync_checkout(checkout, transaction):
    """Trust only authenticated API responses, bound to this exact deposit."""
    try:
        amount = Decimal(str(checkout.get("amount")))
    except (InvalidOperation, TypeError, ValueError):
        return None
    with db_transaction.atomic():
        transaction = WalletTransaction.objects.select_for_update().get(pk=transaction.pk)
        checkout_id = checkout.get("id")
        if (
            transaction.provider != CARD_PROVIDER
            or transaction.transaction_type != WalletTransaction.TYPE_DEPOSIT
            or not isinstance(checkout_id, str) or not checkout_id or len(checkout_id) > 120
            or (transaction.reference and transaction.reference != checkout_id)
            or checkout.get("checkout_reference") != transaction.metadata.get("checkout_reference")
            or not transaction.metadata.get("merchant_code")
            or checkout.get("merchant_code") != transaction.metadata["merchant_code"]
            or checkout.get("currency") != "EUR"
            or not amount.is_finite() or amount != transaction.amount
        ):
            logger.warning("SumUp checkout does not match deposit %s", transaction.pk)
            return None
        status = checkout.get("status")
        transaction.reference = checkout_id
        transaction.metadata = {**transaction.metadata, "sumup_status": status}
        # A verified PAID result wins over earlier FAILED/PENDING notifications.
        # Late or duplicate notifications can never remove or duplicate a credit.
        if status == "PAID":
            transaction.status = WalletTransaction.STATUS_SUCCEEDED
        elif status in {"FAILED", "EXPIRED"} and transaction.status != WalletTransaction.STATUS_SUCCEEDED:
            transaction.status = WalletTransaction.STATUS_FAILED
        transaction.save(update_fields=["reference", "status", "metadata"])
    return transaction


@login_required
def deposit_method(request):
    return render(request, "investments/deposit_method.html", {
        "cards_available": cards_available(),
        "bank_available": all(bank_details().values()),
    })


@login_required
def deposit(request):
    method = request.POST.get("payment_method") or request.GET.get("method", "creditcard")
    if method == "banktransfer":
        if request.method == "POST":
            return bank_transfer(request)
        return redirect("bank_transfer")
    if method != "creditcard":
        return HttpResponseBadRequest("Mode de paiement invalide.")
    form = DepositForm(
        request.POST if request.method == "POST" else None,
        initial={"amount": request.session.get("pending_investment", {}).get("amount")},
        max_amount=Decimal("2000"),
    )
    token = request.POST.get("payment_token") or attempt_token(request.user, "creditcard")
    if request.method == "POST" and form.is_valid():
        if not cards_available():
            messages.error(request, "Le paiement par carte est temporairement indisponible.")
            return redirect("deposit_method")
        try:
            transaction, created = reserve_transaction(request, form, "creditcard")
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            if not created:
                url = transaction.metadata.get("hosted_checkout_url")
                if transaction.status == WalletTransaction.STATUS_PENDING and safe_checkout_url(url):
                    return HttpResponse(status=303, headers={"Location": url})
                messages.info(request, "Cette demande est déjà enregistrée. Consultez votre historique.")
                return redirect("wallet")
            try:
                checkout = create_checkout(
                    settings.SUMUP_API_KEY,
                    merchant_code=transaction.metadata["merchant_code"],
                    amount=transaction.amount,
                    reference=transaction.metadata["checkout_reference"],
                    redirect_url=public_url(request, "sumup_return", transaction.pk),
                    webhook_url=public_url(request, "sumup_webhook", transaction.pk),
                )
                url = checkout.get("hosted_checkout_url")
                if not safe_checkout_url(url) or sync_checkout(checkout, transaction) is None:
                    raise SumUpAPIError("Réponse de paiement invalide.")
                with db_transaction.atomic():
                    transaction = WalletTransaction.objects.select_for_update().get(pk=transaction.pk)
                    transaction.metadata = {**transaction.metadata, "hosted_checkout_url": url}
                    transaction.save(update_fields=["metadata"])
            except SumUpAPIError:
                # A network timeout may occur after checkout creation. Keep it
                # pending so a later verified webhook can still reconcile it.
                logger.warning("Unable to start SumUp checkout for deposit %s", transaction.pk)
                messages.error(request, "Le paiement n'a pas pu démarrer. Aucun solde n'a été crédité. Réessayez plus tard.")
                return redirect("wallet")
            return HttpResponse(status=303, headers={"Location": url})
    return render(request, "investments/deposit.html", {
        "form": form, "balance": wallet_balance(request.user),
        "cards_available": cards_available(), "payment_token": token,
    })


@login_required
def sumup_return(request):
    transaction_id = request.GET.get("transaction_id", "")
    if not transaction_id.isdigit():
        return HttpResponseBadRequest("Transaction invalide.")
    transaction = get_object_or_404(
        WalletTransaction, pk=transaction_id, user=request.user, provider=CARD_PROVIDER,
    )
    if not transaction.reference:
        messages.info(request, "Votre paiement est en cours de vérification.")
        return redirect("wallet")
    try:
        checkout = get_checkout(settings.SUMUP_API_KEY, transaction.reference)
        transaction = sync_checkout(checkout, transaction)
    except SumUpAPIError:
        messages.info(request, "Votre paiement est en cours de vérification.")
        return redirect("wallet")
    if transaction is None:
        return HttpResponseBadRequest("Le paiement ne correspond pas à cette transaction.")
    if transaction.status == WalletTransaction.STATUS_SUCCEEDED:
        messages.success(request, "Paiement confirmé et ajouté à votre porte-monnaie.")
        pending = request.session.get("pending_investment")
        if pending:
            # Let the investor confirm the investment; never spend on a GET.
            return redirect("start_investment", slug=pending["project_slug"])
    elif transaction.status == WalletTransaction.STATUS_FAILED:
        messages.error(request, "Le paiement n'a pas abouti. Vous pouvez réessayer.")
    else:
        messages.info(request, "Votre paiement est en attente de confirmation.")
    return redirect("wallet")


@csrf_exempt
@require_POST
def sumup_webhook(request):
    try:
        event = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest("Notification invalide.")
    if not isinstance(event, dict):
        return HttpResponseBadRequest("Notification invalide.")
    if event.get("event_type") != "CHECKOUT_STATUS_CHANGED":
        return HttpResponse(status=204)
    checkout_id = event.get("id")
    if not isinstance(checkout_id, str) or not checkout_id or len(checkout_id) > 120:
        return HttpResponseBadRequest("Identifiant invalide.")
    query = WalletTransaction.objects.filter(provider=CARD_PROVIDER)
    transaction_id = request.GET.get("transaction_id", "")
    if transaction_id:
        if not transaction_id.isdigit():
            return HttpResponseBadRequest("Transaction invalide.")
        transaction = query.filter(pk=transaction_id).first()
    else:
        transaction = query.filter(reference=checkout_id).first()
    if not transaction:
        return HttpResponse(status=204)
    if transaction.reference and transaction.reference != checkout_id:
        return HttpResponseBadRequest("Identifiant invalide.")
    try:
        checkout = get_checkout(settings.SUMUP_API_KEY, checkout_id)
        if checkout.get("id") != checkout_id or sync_checkout(checkout, transaction) is None:
            return HttpResponseBadRequest("Paiement invalide.")
    except SumUpAPIError:
        # SumUp retries non-2xx responses; don't acknowledge unverified payments.
        return HttpResponse(status=503)
    return HttpResponse(status=204)


@login_required
def bank_transfer(request):
    details = bank_details()
    available = all(details.values())
    form = DepositForm(request.POST if request.method == "POST" else None)
    token = request.POST.get("payment_token") or attempt_token(request.user, "banktransfer")
    transaction = None
    if request.method == "POST" and form.is_valid():
        if not available:
            form.add_error(None, "Le virement bancaire est temporairement indisponible.")
        else:
            try:
                transaction, created = reserve_transaction(request, form, "banktransfer")
            except ValueError as exc:
                form.add_error(None, str(exc))
            else:
                return redirect(f"{reverse('bank_transfer')}?transaction_id={transaction.pk}")
    transaction_id = request.GET.get("transaction_id", "")
    if transaction_id:
        if not transaction_id.isdigit():
            return HttpResponseBadRequest("Transaction invalide.")
        transaction = get_object_or_404(
            WalletTransaction, pk=transaction_id, user=request.user, provider=BANK_PROVIDER,
        )
        details = transaction.metadata.get("bank_details") or details
    return render(request, "investments/bank_transfer.html", {
        "bank": details, "bank_available": available, "form": form,
        "payment_token": token, "transaction": transaction,
    })


def confirm_bank_transfer(transaction_id, admin_user):
    """Called only by the staff admin action after checking bank receipt."""
    with db_transaction.atomic():
        transaction = WalletTransaction.objects.select_for_update().get(pk=transaction_id)
        if transaction.provider != BANK_PROVIDER or transaction.transaction_type != WalletTransaction.TYPE_DEPOSIT or transaction.status != WalletTransaction.STATUS_PENDING:
            return False
        transaction.status = WalletTransaction.STATUS_SUCCEEDED
        transaction.metadata = {
            **transaction.metadata,
            "confirmed_by": admin_user.pk,
            "confirmed_at": timezone.now().isoformat(),
        }
        transaction.save(update_fields=["status", "metadata"])
    return True
