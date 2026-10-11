from django.conf import settings


def analytics(request):
    return {
        "google_analytics_id": settings.GOOGLE_ANALYTICS_ID,
        "google_ads_id": settings.GOOGLE_ADS_ID,
        "site_url": settings.SITE_URL or request.build_absolute_uri("/").rstrip("/"),
    }
