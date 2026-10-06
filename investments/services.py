from decimal import Decimal

from .models import Project, WalletTransaction

CATALOG_PROJECTS = [
    {
        "slug": "l-ondine",
        "title": "L'Ondine",
        "location": "Thonon les Bains",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("1055000.00"),
        "raised_amount": Decimal("860485.00"),
        "annual_return": Decimal("12.00"),
        "duration_months": 24,
        "investors_count": 3492,
        "payment_type": "In-fine",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Opération de marchand de biens sur le bassin lémanique avec forte demande résidentielle.",
        "cover_image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "le-rivoli",
        "title": "Le Rivoli",
        "location": "Paris",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("1500000.00"),
        "raised_amount": Decimal("604343.00"),
        "annual_return": Decimal("12.00"),
        "duration_months": 36,
        "investors_count": 2799,
        "payment_type": "Mensuel",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Opération de marchand de biens au coeur de Paris adossée à un emplacement d'exception.",
        "cover_image_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1494526585095-c41746248156?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "le-marbre",
        "title": "Le Marbre",
        "location": "Strasbourg",
        "operator_type": "Locatif",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("530000.00"),
        "raised_amount": Decimal("390250.00"),
        "annual_return": Decimal("6.00"),
        "duration_months": 60,
        "investors_count": 2083,
        "payment_type": "Mensuel",
        "guarantee": "Hypothèque de 1er rang + Caution personnelle",
        "summary": "Acquisition d'un actif commercial avec rendement locatif récurrent et valorisation à terme.",
        "cover_image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600566752229-250ed79470f8?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600607688066-890987f18a86?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "la-brebise",
        "title": "L'Échoppe",
        "location": "Talence",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("1300000.00"),
        "raised_amount": Decimal("845000.00"),
        "annual_return": Decimal("12.00"),
        "duration_months": 18,
        "investors_count": 2765,
        "payment_type": "In-fine",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Financement d'une opération de rénovation et de valorisation d'un actif de proximité dans une commune dynamique de la métropole bordelaise.",
        "cover_image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1598228723793-52759bba239c?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1560448075-bb485b067938?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1560448205-4d9b3e6bb6db?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "le-chatelain",
        "title": "Le Golf T2",
        "location": "Montauban",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("282000.00"),
        "raised_amount": Decimal("198500.00"),
        "annual_return": Decimal("11.00"),
        "duration_months": 24,
        "investors_count": 1228,
        "payment_type": "In-fine",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Opération résidentielle à proximité d'un environnement vert, avec un montage orienté revente après travaux et sécurisation foncière.",
        "cover_image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1560185127-6ed189bf02f4?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "le-batelier",
        "title": "Le Batelier",
        "location": "Aix-les-Bains",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("965000.00"),
        "raised_amount": Decimal("714589.00"),
        "annual_return": Decimal("12.00"),
        "duration_months": 22,
        "investors_count": 4071,
        "payment_type": "Nantissement de titres",
        "summary": "Financement d'une opération immobilière à fort potentiel en station thermale.",
        "cover_image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600607688960-e095ff83135c?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600210491369-e753d80a41f3?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },    {
        "slug": "le-corner",
        "title": "Le Corner",
        "location": "Nozay",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("522000.00"),
        "raised_amount": Decimal("418000.00"),
        "annual_return": Decimal("11.50"),
        "duration_months": 24,
        "investors_count": 2325,
        "payment_type": "In-fine",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Financement d'une opération immobilière résidentielle en Loire-Atlantique.",
        "cover_image_url": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600047508788-786f3865b4b0?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600585153490-76fb20a32601?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600566753051-f0b89df2dd90?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "le-magicien",
        "title": "Le Magicien",
        "location": "Roubaix",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("1385000.00"),
        "raised_amount": Decimal("948000.00"),
        "annual_return": Decimal("12.00"),
        "duration_months": 24,
        "investors_count": 4998,
        "payment_type": "In-fine",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Rénovation d'un ensemble de logements collectifs à Roubaix.",
        "cover_image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1497366412874-3415097a27e7?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "le-rivage",
        "title": "Le Rivage",
        "location": "Cavalaire-sur-Mer",
        "operator_type": "Opération",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("1851000.00"),
        "raised_amount": Decimal("1265000.00"),
        "annual_return": Decimal("12.00"),
        "duration_months": 20,
        "investors_count": 7340,
        "payment_type": "Hypothèque",
        "summary": "Construction d'une villa de standing vue mer sur la Côte d'Azur.",
        "cover_image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1613977257592-4871e5fcd7c4?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1615873968403-89e068629265?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1615874694520-474822394e73?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
    {
        "slug": "la-tourelle",
        "title": "Le Club",
        "location": "Lyon",
        "operator_type": "Locatif",
        "status": Project.STATUS_OPEN,
        "target_amount": Decimal("740000.00"),
        "raised_amount": Decimal("312000.00"),
        "annual_return": Decimal("7.50"),
        "duration_months": 48,
        "investors_count": 1564,
        "payment_type": "Mensuel",
        "guarantee": "Hypothèque de 1er rang + Caution personnelle",
        "summary": "Acquisition et rénovation d'un immeuble de rapport en coeur de ville pour une valorisation locative durable.",
        "cover_image_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=800&auto=format&fit=crop",
        "gallery_images": [
            "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600210491892-03d54c0aaf87?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=1200&auto=format&fit=crop",
        ],
        "is_featured": True,
    },
]


def _archived_project(slug, title, location, amount, image, status=Project.STATUS_CLOSED):
    return {
        "slug": slug,
        "title": title,
        "location": location,
        "operator_type": "Opération",
        "status": status,
        "target_amount": Decimal(amount),
        "raised_amount": Decimal(amount),
        "annual_return": Decimal("11.50"),
        "duration_months": 24,
        "investors_count": 1800,
        "payment_type": "In-fine",
        "guarantee": "Hypothèque de 1er rang",
        "summary": "Projet immobilier arrivé au terme de sa période de collecte.",
        "cover_image_url": image,
        "gallery_images": [image],
        "is_featured": False,
    }


CATALOG_PROJECTS.extend([
    _archived_project("la-brebise-archive", "La Brebise", "Belgodère", "1300000.00", "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?w=1200&auto=format&fit=crop"),
    _archived_project("le-chatelain-archive", "Le Châtelain", "Château-Arnoux-Saint-Auban", "282000.00", "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=1200&auto=format&fit=crop"),
    _archived_project("le-belvedere", "Le Belvédère", "Annecy", "965000.00", "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?w=1200&auto=format&fit=crop"),
    _archived_project("la-canopee", "La Canopée", "Nantes", "740000.00", "https://images.unsplash.com/photo-1494526585095-c41746248156?w=1200&auto=format&fit=crop"),
    _archived_project("le-square", "Le Square", "Bordeaux", "522000.00", "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&auto=format&fit=crop", Project.STATUS_FUNDED),
    _archived_project("les-terrasses", "Les Terrasses", "Nice", "1385000.00", "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&auto=format&fit=crop", Project.STATUS_FUNDED),
    _archived_project("le-passage", "Le Passage", "Lille", "875000.00", "https://images.unsplash.com/photo-1600566752229-250ed79470f8?w=1200&auto=format&fit=crop"),
    _archived_project("la-villa-verte", "La Villa Verte", "Montpellier", "1180000.00", "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=1200&auto=format&fit=crop"),
    _archived_project("le-clos", "Le Clos", "Dijon", "615000.00", "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=1200&auto=format&fit=crop"),
    _archived_project("l-atelier", "L'Atelier", "Rouen", "930000.00", "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=1200&auto=format&fit=crop", Project.STATUS_FUNDED),
    _archived_project("le-jardin", "Le Jardin", "Toulouse", "1080000.00", "https://images.unsplash.com/photo-1560185127-6ed189bf02f4?w=1200&auto=format&fit=crop"),
    _archived_project("la-residence", "La Résidence", "Reims", "795000.00", "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=1200&auto=format&fit=crop"),
])

PROJECT_OPERATOR_DETAILS = {
    "l-ondine": {
        "name": "Alpes Léman Développement",
        "description": "Opérateur régional spécialisé dans les opérations résidentielles autour du bassin lémanique, avec une expertise sur les biens à rénover proches des zones de tension locative.",
        "track_record": "L'équipe a déjà piloté plusieurs acquisitions avec travaux en Haute-Savoie, en privilégiant des actifs liquides et des sorties par revente lot par lot.",
    },
    "le-rivoli": {
        "name": "Rivoli Patrimoine",
        "description": "Structure parisienne orientée revalorisation d'immeubles de centre-ville et actifs mixtes, avec une forte attention portée à l'emplacement et à la qualité architecturale.",
        "track_record": "Le porteur intervient sur des opérations compactes dans des secteurs établis, avec un suivi notarial et technique renforcé.",
    },
    "le-marbre": {
        "name": "Strasbourg Locatif Invest",
        "description": "Société dédiée à l'acquisition d'actifs générant des revenus locatifs, notamment commerces de proximité et locaux bien placés.",
        "track_record": "La stratégie repose sur des baux existants ou projetés, une analyse de la valeur locative et une gestion patrimoniale prudente.",
    },
    "la-brebise": {
        "name": "Atlantique Réhabilitation",
        "description": "Opérateur bordelais habitué aux échoppes, maisons de ville et actifs de proximité dans les communes de la métropole.",
        "track_record": "Son savoir-faire porte sur la rénovation légère, la redistribution de surfaces et la revente à une clientèle locale.",
    },
    "le-chatelain": {
        "name": "Occitanie Résidentiel",
        "description": "Porteur de projet implanté dans le Sud-Ouest, spécialisé dans les petites opérations résidentielles proches des bassins de vie.",
        "track_record": "L'équipe privilégie les actifs simples à comprendre, avec un budget travaux cadré et une sortie commerciale identifiée dès l'acquisition.",
    },
    "le-batelier": {
        "name": "Savoie Valorisation",
        "description": "Opérateur actif dans les villes thermales et touristiques, avec une approche centrée sur la rénovation d'actifs résidentiels bien situés.",
        "track_record": "Le porteur travaille avec des entreprises locales et sécurise ses sorties via une demande forte pour les biens rénovés près des lacs et centres-villes.",
    },
    "le-corner": {
        "name": "Ouest Promotion",
        "description": "Marchand de biens indépendant intervenant sur des opérations résidentielles en périphérie nantaise et sur des actifs à potentiel de division.",
        "track_record": "Ses opérations sont généralement courtes, avec une stratégie de revente par lots après travaux ciblés.",
    },
    "le-magicien": {
        "name": "Hauts-de-France Immo",
        "description": "Opérateur roubaisien spécialisé dans la rénovation d'immeubles collectifs et la remise sur le marché de logements familiaux.",
        "track_record": "L'équipe combine sourcing local, maîtrise des coûts travaux et connaissance fine du marché locatif de la métropole lilloise.",
    },
    "le-rivage": {
        "name": "Azur Littoral Développement",
        "description": "Porteur de projet centré sur les actifs premium du littoral méditerranéen, avec un positionnement sur des biens de standing.",
        "track_record": "Les opérations visent des emplacements rares, une qualité de finition élevée et une sortie auprès d'acquéreurs patrimoniaux.",
    },
    "la-tourelle": {
        "name": "Lyon Club Patrimoine",
        "description": "Structure lyonnaise orientée locatif urbain, intervenant sur des immeubles de rapport et des actifs à valoriser en coeur de ville.",
        "track_record": "La stratégie repose sur la rénovation, la stabilisation locative et une gestion des surfaces adaptée à la demande locale.",
    },
}


def project_operator_detail(slug):
    return PROJECT_OPERATOR_DETAILS.get(
        slug,
        {
            "name": "Opérateur immobilier sélectionné",
            "description": "Porteur de projet expérimenté dans le montage, le financement et le suivi d'opérations immobilières.",
            "track_record": "Le dossier est analysé selon son emplacement, son budget, ses garanties et sa stratégie de sortie.",
        },
    )


PRESERVE_ON_SYNC = {"raised_amount", "investors_count"}


def ensure_demo_projects():
    catalog_slugs = []
    for data in CATALOG_PROJECTS:
        slug = data["slug"]
        catalog_slugs.append(slug)
        defaults = {key: value for key, value in data.items() if key != "slug"}
        project, created = Project.objects.get_or_create(slug=slug, defaults=defaults)
        if created:
            continue
        for key, value in defaults.items():
            if key in PRESERVE_ON_SYNC:
                continue
            setattr(project, key, value)
        if defaults.get("status") == Project.STATUS_OPEN and project.raised_amount >= project.target_amount:
            project.raised_amount = defaults["raised_amount"]
        project.save()

    Project.objects.exclude(slug__in=catalog_slugs).update(status=Project.STATUS_CLOSED)


def wallet_balance(user):
    if not user.is_authenticated:
        return Decimal("0.00")
    deposits = WalletTransaction.objects.filter(
        user=user,
        transaction_type=WalletTransaction.TYPE_DEPOSIT,
        status=WalletTransaction.STATUS_SUCCEEDED,
    )
    investments = WalletTransaction.objects.filter(
        user=user,
        transaction_type=WalletTransaction.TYPE_INVESTMENT,
        status=WalletTransaction.STATUS_SUCCEEDED,
    )
    refunds = WalletTransaction.objects.filter(
        user=user,
        transaction_type=WalletTransaction.TYPE_REFUND,
        status=WalletTransaction.STATUS_SUCCEEDED,
    )
    deposited = sum((item.amount for item in deposits), Decimal("0.00"))
    invested = sum((item.amount for item in investments), Decimal("0.00"))
    refunded = sum((item.amount for item in refunds), Decimal("0.00"))
    return deposited - invested + refunded
