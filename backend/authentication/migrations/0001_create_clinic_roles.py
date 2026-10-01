from django.db import migrations


CLINIC_ADMIN = "CLINIC_ADMIN"
CLINIC_STAFF = "CLINIC_STAFF"


def create_clinic_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")

    Group.objects.get_or_create(name=CLINIC_ADMIN)
    Group.objects.get_or_create(name=CLINIC_STAFF)


def remove_clinic_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")

    Group.objects.filter(
        name__in=[CLINIC_ADMIN, CLINIC_STAFF]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            create_clinic_roles,
            remove_clinic_roles,
        ),
    ]