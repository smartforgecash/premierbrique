import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import DepositForm, IdentityVerificationForm, InvestmentForm, InvestorProfileForm, SuitabilityForm
from .mollie import MollieAPIError, get_payment as get_mollie_payment
from .models import Investment, InvestorProfile, Project, WalletTransaction
from .services import CATALOG_PROJECTS, ensure_demo_projects, project_operator_detail, wallet_balance


logger = logging.getLogger(__name__)


def _require_verified_email(request):
    return None


def _confirm_investment(user, project, amount):
    investment = Investment.objects.create(
        user=user,
        project=project,
        amount=amount,
        status=Investment.STATUS_CONFIRMED,
        accepted_risks=True,
        signed_subscription=True,
        confirmed_at=timezone.now(),
    )
    WalletTransaction.objects.create(
        user=user,
        transaction_type=WalletTransaction.TYPE_INVESTMENT,
        status=WalletTransaction.STATUS_SUCCEEDED,
        amount=amount,
        reference=f"INV-{investment.pk}",
        provider="wallet",
    )
    project.raised_amount += amount
    project.investors_count += 1
    project.save(update_fields=["raised_amount", "investors_count"])
    return investment


def project_list(request):
    ensure_demo_projects()
    all_projects = Project.objects.all().order_by("-is_featured", "-created_at")
    featured = [p for p in all_projects if p.status == Project.STATUS_OPEN]
    past_queryset = Project.objects.filter(status__in=[Project.STATUS_FUNDED, Project.STATUS_CLOSED]).order_by("-created_at")
    past_page = Paginator(past_queryset, 5).get_page(request.GET.get("page", 1))
    page_range = past_page.paginator.get_elided_page_range(past_page.number, on_each_side=2, on_ends=1)
    return render(
        request,
        "investments/project_list.html",
        {
            "featured": featured,
            "past": past_page.object_list,
            "past_page": past_page,
            "page_range": page_range,
        },
    )


def project_detail(request, slug):
    ensure_demo_projects()
    project = get_object_or_404(Project, slug=slug)
    balance = wallet_balance(request.user) if request.user.is_authenticated else None
    return render(
        request,
        "investments/project_detail.html",
        {
            "project": project,
            "balance": balance,
            "operator_detail": project_operator_detail(project.slug),
        },
    )


@login_required
def profile_onboarding(request):
    blocked = _require_verified_email(request)
    if blocked:
        return blocked
    profile, _ = InvestorProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = InvestorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.save()
            messages.success(request, "Profil investisseur enregistré.")
            next_url = request.GET.get("next") or reverse("suitability_questionnaire")
            return redirect(next_url)
    else:
        form = InvestorProfileForm(instance=profile)
    return render(request, "investments/profile_onboarding.html", {"form": form, "profile": profile})


@login_required
def onboarding(request):
    profile, _ = InvestorProfile.objects.get_or_create(user=request.user)
    return render(request, "investments/onboarding.html", {"profile": profile})


@login_required
def identity_verification(request):
    """Kept for backward compatibility but no longer required in the flow."""
    profile, _ = InvestorProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = IdentityVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.cleaned_data["identity_document"]
            profile.identity_document_name = document.name
            profile.identity_document_type = document.content_type
            profile.identity_document_content = document.read()
            profile.save()
            return redirect("account")
    else:
        form = IdentityVerificationForm()
    return render(request, "investments/identity_verification.html", {"form": form, "profile": profile})


@login_required
def suitability_questionnaire(request):
    blocked = _require_verified_email(request)
    if blocked:
        return blocked
    profile, _ = InvestorProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = SuitabilityForm(request.POST)
        if form.is_valid():
            profile.risk_score = form.score()
            # Auto-approve as soon as the questionnaire is completed — no identity doc required
            if profile.risk_score > 0:
                profile.kyc_status = InvestorProfile.KYC_APPROVED
            profile.save(update_fields=["risk_score", "kyc_status", "updated_at"])
            messages.success(request, "Félicitations ! Votre compte est maintenant activé. Vous pouvez investir.")
            return redirect(request.GET.get("next") or "account")
    else:
        form = SuitabilityForm()
    return render(request, "investments/suitability.html", {"form": form, "profile": profile})


@login_required
def start_investment(request, slug):
    blocked = _require_verified_email(request)
    if blocked:
        return blocked
    ensure_demo_projects()
    project = get_object_or_404(Project, slug=slug)
    profile, _ = InvestorProfile.objects.get_or_create(user=request.user)

    if not project.can_invest:
        messages.error(request, "Ce projet n'est pas ouvert à l'investissement.")
        return redirect(project.get_absolute_url())

    current_balance = wallet_balance(request.user)
    pending = request.session.get("pending_investment")
    pending_amount = None
    if pending and pending.get("project_slug") == project.slug:
        pending_amount = Decimal(str(pending.get("amount", "0")))

    if request.method == "POST":
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            investment.project = project
            if current_balance < investment.amount:
                request.session["pending_investment"] = {
                    "project_slug": project.slug,
                    "amount": str(investment.amount),
                }
                messages.info(request, "Alimentez votre porte-monnaie avant de finaliser l'investissement.")
                return redirect("deposit")

            _confirm_investment(request.user, project, investment.amount)
            request.session.pop("pending_investment", None)
            messages.success(request, "3, 2, 1 Investissement sur votre projet préféré confirmé.")
            return redirect("investment_dashboard")
    else:
        initial = {}
        if pending_amount and pending_amount >= 1:
            initial["amount"] = pending_amount
        form = InvestmentForm(initial=initial)

    return render(
        request,
        "investments/invest.html",
        {
            "project": project,
            "form": form,
            "balance": current_balance,
        },
    )


def _get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        return None
    try:
        import stripe
    except ImportError:
        return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def _confirm_deposit_transaction(transaction):
    transaction.status = WalletTransaction.STATUS_SUCCEEDED
    transaction.save(update_fields=["status"])


def _confirm_pending_investment(request):
    pending = request.session.get("pending_investment")
    if not pending:
        return None
    project = Project.objects.filter(slug=pending.get("project_slug")).first()
    amount = Decimal(str(pending.get("amount", "0")))
    if project and project.can_invest and wallet_balance(request.user) >= amount >= Decimal("1"):
        _confirm_investment(request.user, project, amount)
        request.session.pop("pending_investment", None)
        messages.success(request, "3, 2, 1 Investissement sur votre projet préféré confirmé.")
        return redirect("investment_dashboard")
    return redirect("start_investment", slug=pending["project_slug"])


def _mollie_metadata(payment):
    metadata = payment.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            import json

            metadata = json.loads(metadata)
        except (TypeError, ValueError):
            return {}
    return metadata if isinstance(metadata, dict) else {}


def _sync_mollie_transaction(payment, transaction=None):
    payment_id = str(payment.get("id", ""))
    metadata = _mollie_metadata(payment)
    transaction_id = metadata.get("transaction_id")

    if transaction is None:
        transaction = WalletTransaction.objects.filter(
            reference=payment_id,
            provider__startswith="mollie-",
        ).first()
    if not transaction or str(transaction.pk) != str(transaction_id):
        logger.warning("Rejected Mollie payment %s with invalid transaction metadata", payment_id)
        return None

    amount = payment.get("amount") or {}
    try:
        payment_amount = Decimal(str(amount.get("value")))
    except Exception:
        return None
    if amount.get("currency") != "EUR" or payment_amount != transaction.amount:
        logger.warning("Rejected Mollie payment %s with mismatched amount", payment_id)
        return None

    with db_transaction.atomic():
        transaction = WalletTransaction.objects.select_for_update().get(pk=transaction.pk)
        status = str(payment.get("status", ""))
        transaction.metadata = {
            **transaction.metadata,
            "mollie_status": status,
            "mollie_method": payment.get("method") or transaction.metadata.get("payment_method", ""),
        }
        if status == "paid" and transaction.status == WalletTransaction.STATUS_PENDING:
            transaction.status = WalletTransaction.STATUS_SUCCEEDED
        elif status in {"failed", "canceled", "expired"} and transaction.status == WalletTransaction.STATUS_PENDING:
            transaction.status = WalletTransaction.STATUS_FAILED
        transaction.save(update_fields=["status", "metadata"])
    return transaction


@login_required
def mollie_return(request):
    transaction_id = request.GET.get("transaction_id")
    transaction = WalletTransaction.objects.filter(
        pk=transaction_id,
        user=request.user,
        provider__startswith="mollie-",
    ).first()
    if not transaction or not transaction.reference:
        return HttpResponseBadRequest("Transaction introuvable.")

    try:
        payment = get_mollie_payment(settings.MOLLIE_API_KEY, transaction.reference)
        transaction = _sync_mollie_transaction(payment, transaction)
    except MollieAPIError:
        logger.exception("Unable to verify Mollie payment %s on return", transaction.reference)
        messages.info(request, "Votre paiement est en cours de vérification.")
        return redirect("wallet")

    if not transaction:
        return HttpResponseBadRequest("Le paiement ne correspond pas à cette transaction.")
    if transaction.status == WalletTransaction.STATUS_SUCCEEDED:
        messages.success(request, "Paiement confirmé et ajouté à votre porte-monnaie.")
        pending_redirect = _confirm_pending_investment(request)
        if pending_redirect:
            return pending_redirect
    elif transaction.status == WalletTransaction.STATUS_FAILED:
        messages.error(request, "Le paiement n'a pas abouti. Vous pouvez réessayer.")
    else:
        messages.info(request, "Votre paiement est en attente de confirmation bancaire.")
    return redirect("wallet")


@csrf_exempt
def mollie_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    payment_id = request.POST.get("id", "").strip()
    if not payment_id or len(payment_id) > 120:
        return HttpResponseBadRequest("Identifiant de paiement invalide.")
    try:
        payment = get_mollie_payment(settings.MOLLIE_API_KEY, payment_id)
        _sync_mollie_transaction(payment)
    except MollieAPIError:
        logger.exception("Unable to process Mollie webhook for payment %s", payment_id)
        return HttpResponse(status=502)
    return HttpResponse(status=200)


@login_required
def deposit_success(request):
    session_id = request.GET.get("session_id")
    stripe = _get_stripe_client()
    if not session_id or not stripe:
        return HttpResponseBadRequest("Impossible de vérifier le paiement.")
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status != "paid":
        messages.error(request, "Le paiement n'a pas été confirmé.")
        return redirect("deposit")
    transaction_id = session.metadata.get("transaction_id")
    transaction = WalletTransaction.objects.filter(pk=transaction_id, provider__startswith="stripe").first()
    if not transaction:
        return HttpResponseBadRequest("Transaction introuvable.")
    _confirm_deposit_transaction(transaction)
    messages.success(request, "Percevez vos intérêts. Dépôt confirmé et ajouté à votre porte-monnaie.")
    pending_redirect = _confirm_pending_investment(request)
    if pending_redirect:
        return pending_redirect
    return redirect("wallet")


@login_required
def deposit_cancel(request):
    messages.info(request, "Dépôt annulé. Vous pouvez réessayer ou déposer un autre montant.")
    return redirect("deposit")


@login_required
def wallet(request):
    transactions = WalletTransaction.objects.filter(user=request.user)
    return render(
        request,
        "investments/wallet.html",
        {
            "balance": wallet_balance(request.user),
            "transactions": transactions,
        },
    )


@login_required
def investment_dashboard(request):
    investments = Investment.objects.filter(user=request.user)
    return render(
        request,
        "investments/dashboard.html",
        {
            "investments": investments,
            "balance": wallet_balance(request.user),
        },
    )


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    stripe = _get_stripe_client()
    if not stripe:
        return HttpResponse(status=400)

    event = None
    try:
        if endpoint_secret and sig_header:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        pass
    except ValueError:
        return HttpResponse(status=400)

    if event is None:
        try:
            import json
            data = json.loads(payload)
            event_id = data.get("id")
            if event_id:
                event = stripe.Event.retrieve(event_id)
        except Exception:
            return HttpResponse(status=400)

    if not event:
        return HttpResponse(status=400)

    event_type = event.type
    event_data = event.data.object

    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        session_id = event_data.get("id")
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            transaction_id = session.metadata.get("transaction_id")
            if transaction_id and session.payment_status == "paid":
                transaction = WalletTransaction.objects.filter(pk=transaction_id, provider__startswith="stripe").first()
                if transaction and transaction.status == WalletTransaction.STATUS_PENDING:
                    _confirm_deposit_transaction(transaction)
        except Exception:
            pass

    elif event_type in {"customer_cash_balance_transaction.created", "customer.cash_balance_transaction.created"}:
        txn = event_data
        if txn.get("type") == "funded":
            customer_id = txn.get("customer")
            amount = Decimal(str(txn.get("amount", 0))) / Decimal("100")
            profile = InvestorProfile.objects.filter(stripe_customer_id=customer_id).first()
            if profile:
                ref = txn.get("id")
                exists = WalletTransaction.objects.filter(reference=ref, provider="stripe-bank-transfer").exists()
                if not exists:
                    pending = WalletTransaction.objects.filter(
                        user=profile.user,
                        transaction_type=WalletTransaction.TYPE_DEPOSIT,
                        amount=amount,
                        provider="stripe-bank-transfer",
                        status=WalletTransaction.STATUS_PENDING,
                    ).order_by("created_at").first()
                    if pending:
                        pending.status = WalletTransaction.STATUS_SUCCEEDED
                        pending.reference = ref
                        pending.metadata = {**pending.metadata, "stripe_cash_balance_transaction_id": ref}
                        pending.save(update_fields=["status", "reference", "metadata"])
                    else:
                        WalletTransaction.objects.create(
                            user=profile.user,
                            transaction_type=WalletTransaction.TYPE_DEPOSIT,
                            status=WalletTransaction.STATUS_SUCCEEDED,
                            amount=amount,
                            provider="stripe-bank-transfer",
                            reference=ref,
                        )

    return HttpResponse(status=200)
