from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve

from investments import views as investment_views
from investments import payments
from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("investir", investment_views.project_list, name="investir"),
    path("investir.html", investment_views.project_list, name="investir_page"),
    path("projects.html", investment_views.project_list, name="projects"),
    path("projects/<slug:slug>/", investment_views.project_detail, name="project_detail"),
    path("projects/<slug:slug>/invest/", investment_views.start_investment, name="start_investment"),
    path("onboarding/profile/", investment_views.profile_onboarding, name="profile_onboarding"),
    path("onboarding/", investment_views.onboarding, name="onboarding"),
    path("onboarding/identity/", investment_views.identity_verification, name="identity_verification"),
    path("onboarding/questionnaire/", investment_views.suitability_questionnaire, name="suitability_questionnaire"),
    path("wallet/deposit/method/", payments.deposit_method, name="deposit_method"),
    path("wallet/deposit/bank-transfer/", payments.bank_transfer, name="bank_transfer"),
    path("wallet/deposit/", payments.deposit, name="deposit"),
    path("payments/sumup/return/", payments.sumup_return, name="sumup_return"),
    path("payments/sumup/webhook/", payments.sumup_webhook, name="sumup_webhook"),
    # Legacy callbacks settle existing deposits; new payments use SumUp.
    path("payments/mollie/return/", investment_views.mollie_return, name="mollie_return"),
    path("payments/mollie/webhook/", investment_views.mollie_webhook, name="mollie_webhook"),
    path("wallet/deposit/success/", investment_views.deposit_success, name="deposit_success"),
    path("wallet/deposit/cancel/", investment_views.deposit_cancel, name="deposit_cancel"),
    path("wallet/deposit/webhook/", investment_views.stripe_webhook, name="stripe_webhook"),
    # Alternate webhook path used for local Stripe CLI forwarding
    path("stripe/webhook/", investment_views.stripe_webhook, name="stripe_webhook_root"),
    path("wallet/", investment_views.wallet, name="wallet"),
    path("investments/", investment_views.investment_dashboard, name="investment_dashboard"),
    path("login.html", views.login_page, name="login"),
    path("login/google/", views.google_login_page, name="google_login"),
    path("signup-email.html", views.signup_email_page, name="signup_email"),
    path("logout/", views.logout_page, name="logout"),
    path("account/", views.account_page, name="account"),
    path("auth/session.json", views.session_status, name="session_status"),
    path("css/<path:path>", serve, {"document_root": settings.BASE_DIR / "css"}),
    path("js/<path:path>", serve, {"document_root": settings.BASE_DIR / "js"}),
    re_path(r"^(?P<template_name>[-\w]+\.html)$", views.static_page, name="static_page"),
    path("auth/", include("social_django.urls", namespace="social")),
]
