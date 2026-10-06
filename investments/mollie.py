import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MOLLIE_API_BASE_URL = "https://api.mollie.com/v2"


class MollieAPIError(Exception):
    """Raised when Mollie cannot create or retrieve a payment."""


def _request(api_key, method, path, payload=None, idempotency_key=""):
    if not api_key:
        raise MollieAPIError("Mollie n'est pas configuré.")

    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "PremierBrique/1.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    request = Request(
        f"{MOLLIE_API_BASE_URL}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            error = json.loads(exc.read().decode("utf-8")).get("detail", "")
        except (ValueError, UnicodeDecodeError):
            error = ""
        raise MollieAPIError(error or "Mollie a refusé la demande de paiement.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise MollieAPIError("Le service Mollie est temporairement inaccessible.") from exc


def create_payment(api_key, *, amount, method, description, redirect_url, webhook_url, metadata, idempotency_key):
    return _request(
        api_key,
        "POST",
        "/payments",
        {
            "amount": {"currency": "EUR", "value": f"{amount:.2f}"},
            "description": description,
            "method": method,
            "redirectUrl": redirect_url,
            "webhookUrl": webhook_url,
            "locale": "fr_FR",
            "metadata": metadata,
        },
        idempotency_key=idempotency_key,
    )


def get_payment(api_key, payment_id):
    return _request(api_key, "GET", f"/payments/{payment_id}")
