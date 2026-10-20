"""Run write/read in separate application processes around a database restart.
Usage: python scripts/verify_persistence.py write|read
Uses only configured validation database. Never run write against real data.
"""

import os, sys, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from clinic.services.clinic import ClinicService
from clinic.data.persistent import PersistentClinicRepository
from clinic.services.inventory import inventory_service

repo = PersistentClinicRepository()
service = ClinicService(repo)
manifest = (
    root
    / ".runtime"
    / ("restart-" + os.environ.get("DB_ENGINE", "sqlite").split(".")[-1] + ".json")
)
if sys.argv[1] == "write":
    entries = {}
    for kind, data in [
        ("health_record", {"student_id": "2026-0001", "blood_type": "O+"}),
        (
            "consultation",
            {"student_id": "2026-0001", "chief_complaint": "Restart verification"},
        ),
        ("health_status", {"student_id": "2026-0001", "status": "CLEARED"}),
    ]:
        row = getattr(service, "create_" + kind)(data)
        entries[kind] = row[repo.models[kind]._meta.pk.name]
    row = service.create_dispensation(
        {
            "student_id": "2026-0001",
            "medicine_id": "MED-0001",
            "quantity": 1,
            "reason": "Restart verification",
        }
    )
    entries["dispensation"] = row["dispensation_id"]
    entries["transaction"] = row["inventory_transaction_id"]
    if getattr(inventory_service, "durable", False):
        entries["inventory_stock"] = inventory_service.get_medicine("MED-0001")[
            "quantity_in_stock"
        ]
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(json.dumps(entries), encoding="utf-8")
    print("Wrote all four Clinic resource kinds and Inventory transaction reference.")
else:
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    for kind, key in entries.items():
        if kind in ("transaction", "inventory_stock"):
            continue
        row = getattr(repo, "get_" + kind)(key)
        assert row and row["student_id"] == "2026-0001", kind
        if kind == "dispensation":
            assert row["inventory_transaction_id"] == entries["transaction"]
    if "inventory_stock" in entries:
        assert (
            inventory_service.get_medicine("MED-0001")["quantity_in_stock"]
            == entries["inventory_stock"]
        )
        assert entries["transaction"] in inventory_service._transactions
        print(
            "PASS: durable simulated Inventory stock and transaction survive process restart."
        )
    print(
        "PASS: new application process read all four kinds and unchanged Inventory reference after restart."
    )
