"""Create synthetic credentials ONLY in an explicitly disposable database."""

import os
import sys
from pathlib import Path

if os.environ.get("CLINIC_DISPOSABLE") != "1":
    raise SystemExit("Set CLINIC_DISPOSABLE=1 for a disposable validation database.")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from authentication.models import OwnerRegistration

User = get_user_model()
owner = User.objects.create_superuser(
    username=os.environ["CLINIC_TEST_USERNAME"],
    password=os.environ["CLINIC_TEST_PASSWORD"],
)
OwnerRegistration.objects.update_or_create(pk=1, defaults={"owner": owner})
if os.environ.get("CLINIC_TEST_LIMITS") == "1":
    group, _ = Group.objects.get_or_create(name="CLINIC_STAFF")
    for i in range(11):
        user = User.objects.create_user(username=f"seedstaff_{i:02}", password=None)
        user.groups.add(group)
print("Disposable validation accounts provisioned; credentials omitted.")
