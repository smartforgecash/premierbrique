from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import TemplateDoesNotExist
from django.urls import reverse

from investments.models import Investment, InvestorProfile, Project
from investments.services import ensure_demo_projects, wallet_balance
from .page_content import PUBLIC_PAGES


def home(request):
    return render(request, "index.html")


def health(request):
    return HttpResponse("ok", content_type="text/plain")


def robots_txt(request):
    site_url = settings.SITE_URL or request.build_absolute_uri("/").rstrip("/")
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /account/",
            "Disallow: /wallet/",
            "Disallow: /onboarding/",
            "Disallow: /auth/",
            f"Sitemap: {site_url}/sitemap.xml",
        ]
    )
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    site_url = settings.SITE_URL or request.build_absolute_uri("/").rstrip("/")
    paths = [
        "",
        "investir",
        "a-propos.html",
        "blog.html",
        "se-financer.html",
        "performances.html",
        "risques.html",
    ]
    urls = "".join(
        f"<url><loc>{site_url}/{path}</loc></url>"
        for path in paths
    )
    content = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(content, content_type="application/xml")


def static_page(request, template_name):
    if template_name == "verify-email.html":
        return redirect("account" if request.user.is_authenticated else "signup_email")
    if template_name in PUBLIC_PAGES:
        return render(request, "public-page.html", {"page": PUBLIC_PAGES[template_name]})
    try:
        return render(request, template_name)
    except TemplateDoesNotExist:
        return render(request, "index.html", status=404)


def login_page(request):
    if request.method == "POST":
        email = request.POST.get("user[email]", "").strip().lower()
        password = request.POST.get("user[password]", "")
        next_url = request.POST.get("next") or request.GET.get("next") or "account"
        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Adresse email ou mot de passe incorrect.")
            return render(request, "login.html", status=400)

        login(request, user)
        messages.success(request, "Connexion réussie. Accédez aux opportunités immobilières.")
        return redirect(next_url)

    return render(request, "login.html")


def google_login_page(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse("social:begin", args=["google-oauth2"]))


def signup_email_page(request):
    if request.method == "POST":
        email = request.POST.get("user_registration[email]", "").strip().lower()
        password = request.POST.get("user_registration[password]", "")
        password_confirmation = request.POST.get("user_registration[password_confirmation]", "")
        terms_accepted = request.POST.get("user_registration[terms_accepted]") == "1"

        if not email or not password or not terms_accepted:
            messages.error(request, "Veuillez saisir votre email, un mot de passe et accepter les conditions.")
            return render(request, "signup-email.html", status=400)
        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, "signup-email.html", status=400)
        if password != password_confirmation:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "signup-email.html", status=400)

        try:
            user = User.objects.create_user(username=email, email=email, password=password)
        except IntegrityError:
            messages.error(request, "Un compte existe déjà avec cette adresse email.")
            return render(request, "signup-email.html", status=400)

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Compte créé. Bienvenue dans votre espace investisseur.")
        return redirect("account")

    return render(request, "signup-email.html")


def logout_page(request):
    logout(request)
    messages.info(request, "Déconnexion réussie.")
    return redirect("home")


@login_required
def account_page(request):
    ensure_demo_projects()
    profile, _ = InvestorProfile.objects.get_or_create(user=request.user)
    investment_qs = Investment.objects.filter(user=request.user).select_related("project")
    investments = investment_qs[:5]
    total_invested = sum((investment.amount for investment in investment_qs), 0)
    return render(
        request,
        "investments/account.html",
        {
            "profile": profile,
            "onboarding_steps": profile.onboarding_completed_steps,
            "balance": wallet_balance(request.user),
            "investments": investments,
            "investments_count": investment_qs.count(),
            "total_invested": total_invested,
            "featured_projects": Project.objects.filter(status=Project.STATUS_OPEN).order_by("-is_featured", "-created_at")[:10],
        },
    )


def session_status(request):
    user = request.user
    payload = {
        "authenticated": user.is_authenticated,
        "email": user.email or user.username if user.is_authenticated else "",
        "email_verified": user.is_authenticated,
        "messages": [
            {"level": message.tags, "text": str(message)}
            for message in messages.get_messages(request)
        ],
    }
    return JsonResponse(payload)
