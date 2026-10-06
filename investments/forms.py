from django import forms

from .models import InvestorProfile, Investment, WalletTransaction


class InvestorProfileForm(forms.ModelForm):
    class Meta:
        model = InvestorProfile
        fields = [
            "investor_type",
            "full_name",
            "phone",
            "birth_date",
            "country",
            "nationality",
            "birth_place",
            "birth_country",
            "company_name",
            "company_type",
            "company_siret",
            "representative_role",
            "address",
            "city",
            "postal_code",
            "accepted_terms",
            "accepted_risks",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "accepted_terms": forms.CheckboxInput(),
            "accepted_risks": forms.CheckboxInput(),
            "investor_type": forms.RadioSelect(),
        }
        labels = {
            "investor_type": "Vous êtes :",
            "full_name": "Nom complet (ou Représentant légal)",
            "phone": "Téléphone",
            "birth_date": "Date de naissance",
            "country": "Pays de résidence",
            "nationality": "Nationalité",
            "birth_place": "Ville de naissance",
            "birth_country": "Pays de naissance",
            "company_name": "Dénomination sociale (Nom de la société)",
            "company_type": "Forme juridique (SCI, SAS, SARL, etc.)",
            "company_siret": "Numéro SIRET / SIREN",
            "representative_role": "Qualité du représentant (Gérant, Président...)",
            "address": "Adresse",
            "city": "Ville",
            "postal_code": "Code postal",
            "accepted_terms": "J'accepte les CGU de La Première Brique",
            "accepted_risks": "Je comprends que tout investissement comporte un risque de perte en capital",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make conditional fields not required by default in form definition
        conditional_fields = [
            "birth_date",
            "nationality",
            "birth_place",
            "birth_country",
            "company_name",
            "company_type",
            "company_siret",
            "representative_role",
        ]
        for field in conditional_fields:
            if field in self.fields:
                self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        investor_type = cleaned_data.get("investor_type")

        if investor_type == InvestorProfile.INVESTOR_COMPANY:
            company_fields = ["company_name", "company_type", "company_siret", "representative_role"]
            for field in company_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Ce champ est obligatoire pour une personne morale.")
        else:
            individual_fields = ["birth_date", "nationality", "birth_place", "birth_country"]
            for field in individual_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Ce champ est obligatoire pour une personne physique.")
        return cleaned_data


class SuitabilityForm(forms.Form):
    investment_experience = forms.ChoiceField(
        label="Votre expérience en investissement",
        choices=[
            ("beginner", "Débutant"),
            ("intermediate", "Quelques investissements"),
            ("advanced", "Investisseur expérimenté"),
        ],
        widget=forms.RadioSelect,
    )
    investment_goal = forms.ChoiceField(
        label="Votre objectif principal",
        choices=[
            ("diversify", "Diversifier mon épargne"),
            ("income", "Chercher des revenus réguliers"),
            ("growth", "Chercher un rendement élevé"),
        ],
        widget=forms.RadioSelect,
    )
    loss_capacity = forms.ChoiceField(
        label="Quelle perte pouvez-vous supporter ?",
        choices=[
            ("low", "Aucune ou très faible"),
            ("medium", "Une partie limitée"),
            ("high", "Une perte importante sur une petite poche d'investissement"),
        ],
        widget=forms.RadioSelect,
    )

    def score(self):
        values = self.cleaned_data
        score = 1
        if values.get("investment_experience") == "advanced":
            score += 2
        elif values.get("investment_experience") == "intermediate":
            score += 1
        if values.get("loss_capacity") == "high":
            score += 2
        elif values.get("loss_capacity") == "medium":
            score += 1
        return score


class IdentityVerificationForm(forms.Form):
    identity_document = forms.FileField(
        label="Pièce d'identité",
        help_text="Carte nationale d'identité, passeport ou titre de séjour (PDF, JPG ou PNG, 8 Mo maximum).",
    )

    def clean_identity_document(self):
        document = self.cleaned_data["identity_document"]
        if document.content_type not in {"application/pdf", "image/jpeg", "image/png"}:
            raise forms.ValidationError("Utilisez un fichier PDF, JPG ou PNG.")
        if document.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Le fichier ne doit pas dépasser 8 Mo.")
        return document


class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ["amount", "accepted_risks", "signed_subscription"]
        labels = {
            "amount": "Montant à investir",
            "accepted_risks": "Je reconnais avoir lu les risques du projet",
            "signed_subscription": "Je confirme vouloir souscrire à ce projet",
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount < 1:
            raise forms.ValidationError("Le montant minimum est de 1 €.")
        return amount


class DepositForm(forms.ModelForm):
    def __init__(self, *args, max_amount=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_amount = max_amount

    class Meta:
        model = WalletTransaction
        fields = ["amount"]
        labels = {"amount": "Montant à déposer"}

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount < 1:
            raise forms.ValidationError("Le dépôt minimum est de 1 €.")
        if self.max_amount and amount > self.max_amount:
            raise forms.ValidationError(f"Le montant maximum est de {self.max_amount:,.0f} €.")
        return amount
