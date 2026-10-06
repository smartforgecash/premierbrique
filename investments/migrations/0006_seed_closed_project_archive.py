from decimal import Decimal

from django.db import migrations


def seed_closed_archive(apps, schema_editor):
    Project = apps.get_model("investments", "Project")
    image_url = "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=900&auto=format&fit=crop"
    projects = []
    for number in range(1, 139):
        slug = f"archive-cloturee-{number:03d}"
        if Project.objects.filter(slug=slug).exists():
            continue
        projects.append(Project(
            slug=slug,
            title=f"Projet clôturé {number:03d}",
            location="France",
            operator_type="Opération",
            status="closed",
            target_amount=Decimal("0.00"),
            raised_amount=Decimal("0.00"),
            annual_return=Decimal("0.00"),
            duration_months=1,
            investors_count=0,
            payment_type="Archivé",
            guarantee="",
            summary="Projet clôturé et conservé dans les archives de la plateforme.",
            cover_image_url=image_url,
            gallery_images=[image_url],
            is_featured=False,
        ))
    Project.objects.bulk_create(projects, batch_size=100)


def remove_closed_archive(apps, schema_editor):
    Project = apps.get_model("investments", "Project")
    Project.objects.filter(slug__startswith="archive-cloturee-").delete()


class Migration(migrations.Migration):
    dependencies = [("investments", "0005_investorprofile_stripe_customer_id")]
    operations = [migrations.RunPython(seed_closed_archive, remove_closed_archive)]
