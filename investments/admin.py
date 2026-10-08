from io import BytesIO

from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path, reverse
from django.utils.html import format_html

from .payments import confirm_bank_transfer
from .models import EmailVerificationCode, Investment, InvestorProfile, Project, WalletTransaction


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "target_amount", "raised_amount", "annual_return", "duration_months")
    list_filter = ("status", "is_featured")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "kyc_status", "identity_document_link", "risk_score", "updated_at")
    list_filter = ("kyc_status", "accepted_terms", "accepted_risks")
    readonly_fields = ("identity_document_link",)
    actions = ("approve_identity", "reject_identity")

    def get_urls(self):
        return [
            path(
                "<int:profile_id>/identity-document/",
                self.admin_site.admin_view(self.download_identity_document),
                name="investments_investorprofile_identity_document",
            ),
        ] + super().get_urls()

    @admin.display(description="Pièce d'identité")
    def identity_document_link(self, profile):
        if not profile.identity_document_content:
            return "Aucun document"
        url = reverse("admin:investments_investorprofile_identity_document", args=[profile.pk])
        return format_html('<a href="{}">Télécharger le document</a>', url)

    def download_identity_document(self, request, profile_id):
        profile = self.get_object(request, profile_id)
        if not profile or not profile.identity_document_content:
            raise Http404("Document introuvable")
        response = FileResponse(
            BytesIO(bytes(profile.identity_document_content)),
            content_type=profile.identity_document_type or "application/octet-stream",
            as_attachment=True,
            filename=profile.identity_document_name or f"identite-{profile.pk}",
        )
        response["X-Content-Type-Options"] = "nosniff"
        return response

    @admin.action(description="Approuver les identités sélectionnées")
    def approve_identity(self, request, queryset):
        eligible = queryset.exclude(identity_document_content__isnull=True)
        updated = eligible.update(kyc_status=InvestorProfile.KYC_APPROVED)
        self.message_user(request, f"{updated} identité(s) approuvée(s).")

    @admin.action(description="Refuser les identités sélectionnées")
    def reject_identity(self, request, queryset):
        updated = queryset.update(kyc_status=InvestorProfile.KYC_REJECTED)
        self.message_user(request, f"{updated} identité(s) refusée(s).")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "status", "amount", "provider", "reference", "created_at")
    search_fields = ("reference", "user__username", "user__email")
    readonly_fields = ("user", "transaction_type", "amount", "provider", "reference", "metadata", "status", "created_at")
    actions = ("confirm_received_transfers",)
    list_filter = ("transaction_type", "status", "provider")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Confirmer les virements reçus sur le compte bancaire", permissions=["change"])
    def confirm_received_transfers(self, request, queryset):
        count = sum(confirm_bank_transfer(pk, request.user) for pk in queryset.values_list("pk", flat=True))
        self.message_user(request, f"{count} virement(s) confirmé(s) après réception bancaire.")


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "amount", "status", "created_at")
    list_filter = ("status", "project")


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "used_at")
    list_filter = ("used_at",)
