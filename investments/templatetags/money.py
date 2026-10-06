from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def euro(value, decimals=2):
    try:
        decimal_places = int(decimals)
    except (TypeError, ValueError):
        decimal_places = 2

    try:
        amount = Decimal(str(value if value not in (None, "") else "0"))
    except (InvalidOperation, ValueError):
        amount = Decimal("0")

    formatted = f"{amount:,.{decimal_places}f}"
    formatted = formatted.replace(",", " ").replace(".", ",")
    return f"{formatted} \u20ac"
