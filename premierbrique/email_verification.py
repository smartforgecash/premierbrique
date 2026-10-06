from django.conf import settings
from django.core.mail import send_mail

from investments.models import EmailVerificationCode


def user_email_is_verified(user):
    return bool(user.is_authenticated and user.email and user.email_codes.filter(used_at__isnull=False).exists())


def send_verification_code(user):
    verification = EmailVerificationCode.create_for_user(user)
    send_mail(
        "Votre code de vérification Premier Brique",
        (
            f"Bonjour,\n\n"
            f"Votre code de vérification est : {verification.code}\n\n"
            "Ce code expire dans 15 minutes.\n\n"
            "Premier Brique"
        ),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return verification
