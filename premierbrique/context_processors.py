from django.conf import settings


def analytics(request):
    match = getattr(request, "resolver_match", None)
    page_view = ""
    if (match and match.url_name in {"investir", "investir_page", "projects"}
            and settings.GOOGLE_ADS_ID and settings.GOOGLE_ADS_PAGE_VIEW_LABEL):
        page_view = f"{settings.GOOGLE_ADS_ID}/{settings.GOOGLE_ADS_PAGE_VIEW_LABEL}"
    return {
        "google_analytics_id": settings.GOOGLE_ANALYTICS_ID,
        "google_ads_id": settings.GOOGLE_ADS_ID,
        "google_ads_page_view": page_view,
        "site_url": settings.SITE_URL or request.build_absolute_uri("/").rstrip("/"),
    }
