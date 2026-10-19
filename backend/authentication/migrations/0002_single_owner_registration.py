from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def adopt_existing_owner(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    Registration = apps.get_model('authentication', 'OwnerRegistration')
    Group = apps.get_model('auth', 'Group')
    Session = apps.get_model('sessions', 'Session')
    owners = list(User.objects.filter(is_superuser=True).order_by('-is_active', 'pk'))
    legacy_tests = {'integration_check', 'password_flow_validation', 'account_flow_validation', 'lifecycle_flow_validation'}
    preferred = [u for u in owners if u.username not in legacy_tests]
    chosen = next((u for name in ['clinic_owner', 'demo_admin'] for u in owners if u.username == name), (preferred or owners or [None])[0])
    if chosen:
        extras = [u.pk for u in owners if u.pk != chosen.pk]
        if extras:
            # Retain legacy accounts without retaining multiple Owner identities.
            User.objects.filter(pk__in=extras).update(is_superuser=False, is_staff=False, is_active=False)
            staff, _ = Group.objects.get_or_create(name='CLINIC_STAFF')
            for user in owners:
                if user.pk in extras:
                    user.groups.clear()
                    user.groups.add(staff)
            # All existing sessions are re-authenticated after the role migration.
            Session.objects.all().delete()
        Registration.objects.update_or_create(pk=1, defaults={'owner_id': chosen.pk})
    else:
        Registration.objects.get_or_create(pk=1)


def add_unique_owner_index(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    q = schema_editor.quote_name
    schema_editor.execute(f'CREATE UNIQUE INDEX {q("clinic_single_owner")} ON {q(User._meta.db_table)} ({q("is_superuser")}) WHERE {q("is_superuser")}')


def remove_unique_owner_index(apps, schema_editor):
    schema_editor.execute('DROP INDEX clinic_single_owner')


class Migration(migrations.Migration):
    dependencies = [('authentication', '0001_create_clinic_roles'), ('sessions', '0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='OwnerRegistration', fields=[
            ('id', models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False, serialize=False)),
            ('owner', models.OneToOneField(to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='owner_registration')),
        ], options={'constraints': [models.CheckConstraint(condition=models.Q(id=1), name='single_owner_registration_row')]}),
        migrations.RunPython(adopt_existing_owner, migrations.RunPython.noop),
        migrations.RunPython(add_unique_owner_index, remove_unique_owner_index),
    ]
