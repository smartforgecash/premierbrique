from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve

from .context_processors import analytics


@override_settings(
    GOOGLE_ADS_ID="AW-18397712539",
    GOOGLE_ADS_PAGE_VIEW_LABEL="pDnVCKOztpgdEJuh28RE",
    GOOGLE_ANALYTICS_ID="",
    SITE_URL="https://la-premiere-brique.com",
)
class AnalyticsPageViewTests(SimpleTestCase):
    def render_tag(self, path):
        request = RequestFactory().get(path)
        request.resolver_match = resolve(request.path)
        return render_to_string("analytics.html", analytics(request))

    def test_listing_routes_mark_conversion_page(self):
        for path in ("/investir", "/investir?gclid=test", "/investir.html", "/projects.html"):
            with self.subTest(path=path):
                html = self.render_tag(path)
                self.assertIn('data-google-ads-page-view="AW-18397712539/pDnVCKOztpgdEJuh28RE"', html)
                self.assertEqual(html.count("/js/google-tag.js?v=2"), 1)

    def test_other_pages_do_not_count_as_listing_visits(self):
        for path in ("/", "/login.html", "/signup-email.html", "/wallet/", "/investments/",
                     "/payments/sumup/return/", "/projects/example/", "/admin/login/"):
            with self.subTest(path=path):
                self.assertNotIn("data-google-ads-page-view", self.render_tag(path))

    def test_disabled_ads_or_label_does_not_emit_conversion_marker(self):
        with override_settings(GOOGLE_ADS_PAGE_VIEW_LABEL=""):
            self.assertNotIn("data-google-ads-page-view", self.render_tag("/investir"))
        with override_settings(GOOGLE_ADS_ID=""):
            self.assertNotIn("data-google-ads-page-view", self.render_tag("/investir"))
