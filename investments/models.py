from datetime import timedelta
from decimal import Decimal
import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class InvestorProfile(models.Model):
    KYC_PENDING = "pending"
    KYC_REVIEW = "review"
    KYC_APPROVED = "approved"
    KYC_REJECTED = "rejected"
    KYC_CHOICES = [
        (KYC_PENDING, "A compléter"),
        (KYC_REVIEW, "En vérification"),
        (KYC_APPROVED, "Validé"),
        (KYC_REJECTED, "Refusé"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    INVESTOR_INDIVIDUAL = "individual"
    INVESTOR_COMPANY = "company"
    INVESTOR_TYPE_CHOICES = [
        (INVESTOR_INDIVIDUAL, "Personne physique (Individu)"),
        (INVESTOR_COMPANY, "Personne morale (Société)"),
    ]
    investor_type = models.CharField(max_length=20, choices=INVESTOR_TYPE_CHOICES, default=INVESTOR_INDIVIDUAL)
    
    # Personal/Representative details
    full_name = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=80, blank=True)
    nationality = models.CharField(max_length=80, blank=True)
    birth_place = models.CharField(max_length=120, blank=True)
    birth_country = models.CharField(max_length=80, blank=True)
    
    # Company details (for investor_type == 'company')
    company_name = models.CharField(max_length=160, blank=True)
    company_type = models.CharField(max_length=40, blank=True)
    company_siret = models.CharField(max_length=40, blank=True)
    representative_role = models.CharField(max_length=80, blank=True)
    
    # Address details
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=40, blank=True)
    
    # Virtual IBAN details from Stripe
    iban = models.CharField(max_length=80, blank=True)
    bic = models.CharField(max_length=40, blank=True)
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_holder_name = models.CharField(max_length=160, blank=True)
    
    risk_score = models.PositiveSmallIntegerField(default=0)
    kyc_status = models.CharField(max_length=20, choices=KYC_CHOICES, default=KYC_PENDING)
    accepted_terms = models.BooleanField(default=False)
    accepted_risks = models.BooleanField(default=False)
    identity_document_name = models.CharField(max_length=255, blank=True)
    identity_document_type = models.CharField(max_length=100, blank=True)
    identity_document_content = models.BinaryField(null=True, blank=True, editable=False)
    stripe_customer_id = models.CharField(max_length=120, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.get_username()

    @property
    def initials(self):
        parts = self.full_name.split()
        if parts:
            if len(parts) > 1:
                return f"{parts[-1][0]}{parts[0][0]}".upper()
            return parts[0][0].upper()
        return ""

    @property
    def is_complete(self):
        if self.investor_type == self.INVESTOR_COMPANY:
            required = [
                self.company_name,
                self.company_type,
                self.company_siret,
                self.representative_role,
                self.full_name,
                self.phone,
                self.address,
                self.city,
                self.postal_code,
            ]
        else:
            required = [
                self.full_name,
                self.phone,
                self.birth_date,
                self.country,
                self.birth_place,
                self.birth_country,
                self.address,
                self.city,
                self.postal_code,
            ]
        return all(required) and self.accepted_terms and self.accepted_risks

    @property
    def has_identity_document(self):
        return bool(self.identity_document_name and self.identity_document_content)

    @property
    def onboarding_completed_steps(self):
        # 3 steps: 1 = account created (always), 2 = profile complete, 3 = suitability done
        return 1 + int(self.is_complete) + int(self.risk_score > 0)


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.code}"

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        return cls.objects.create(
            user=user,
            code=f"{secrets.randbelow(1000000):06d}",
            expires_at=timezone.now() + timedelta(minutes=15),
        )

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at >= timezone.now()

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class Project(models.Model):
    STATUS_OPEN = "open"
    STATUS_SOON = "soon"
    STATUS_FUNDED = "funded"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Collecte en cours"),
        (STATUS_SOON, "Ouverture prochaine"),
        (STATUS_FUNDED, "Financé"),
        (STATUS_CLOSED, "Clôturé"),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    location = models.CharField(max_length=160)
    operator_type = models.CharField(max_length=120, default="Marchand de biens")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    raised_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    annual_return = models.DecimalField(max_digits=5, decimal_places=2)
    duration_months = models.PositiveSmallIntegerField()
    investors_count = models.PositiveIntegerField(default=0)
    payment_type = models.CharField(max_length=80, default="In-fine")
    guarantee = models.CharField(max_length=160, default="Hypothèque de 1er rang")
    summary = models.TextField()
    cover_image_url = models.URLField(blank=True)
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of image URLs for the project gallery")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("project_detail", kwargs={"slug": self.slug})

    @property
    def progress_percent(self):
        if not self.target_amount:
            return 0
        return min(100, int((self.raised_amount / self.target_amount) * 100))

    @property
    def can_invest(self):
        return self.status == self.STATUS_OPEN and self.raised_amount < self.target_amount


class WalletTransaction(models.Model):
    TYPE_DEPOSIT = "deposit"
    TYPE_INVESTMENT = "investment"
    TYPE_REFUND = "refund"
    TYPE_CHOICES = [
        (TYPE_DEPOSIT, "Dépôt"),
        (TYPE_INVESTMENT, "Investissement"),
        (TYPE_REFUND, "Remboursement"),
    ]
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_SUCCEEDED, "Réussi"),
        (STATUS_FAILED, "Échoué"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=120, blank=True)
    provider = models.CharField(max_length=60, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} {self.transaction_type} {self.amount}"


class Investment(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING_PAYMENT = "pending_payment"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Brouillon"),
        (STATUS_PENDING_PAYMENT, "Paiement en attente"),
        (STATUS_CONFIRMED, "Confirmé"),
        (STATUS_CANCELLED, "Annulé"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    accepted_risks = models.BooleanField(default=False)
    signed_subscription = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.project} - {self.amount}"
