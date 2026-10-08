"""Server-side SumUp Hosted Checkout client."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class SumUpAPIError(Exception):
    """SumUp could not create or verify a checkout."""


def _request(api_key, method, path, payload=None):
    if not api_key:
        raise SumUpAPIError("SumUp n'est pas configuré.")
    request = Request(
        f"https://api.sumup.com/v0.1{path}",
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "PremierBrique/1.0",
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("Invalid checkout response")
        return result
    except (HTTPError, URLError, OSError, ValueError) as exc:
        raise SumUpAPIError("Le service de paiement est temporairement indisponible.") from exc


def create_checkout(api_key, *, merchant_code, amount, reference, redirect_url, webhook_url):
    return _request(api_key, "POST", "/checkouts", {
        "amount": float(amount),
        "currency": "EUR",
        "merchant_code": merchant_code,
        "checkout_reference": reference,
        "description": f"Dépôt PREMIERE BRIQUE {reference}",
        "redirect_url": redirect_url,
        "return_url": webhook_url,
        "hosted_checkout": {"enabled": True},
    })


def get_checkout(api_key, checkout_id):
    return _request(api_key, "GET", f"/checkouts/{quote(checkout_id, safe='')}")
