import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from datetime import timedelta
from clinic.services.inventory import MockInventoryService, InsufficientStockError
from clinic.services.durable_inventory import DurableInventoryMixin
from clinic.models import OperationReceipt


class Provider(DurableInventoryMixin, MockInventoryService):
    pass


class DurableInventoryTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "inventory.sqlite3"
        self.provider = Provider(self.path)

    def test_restart_preserves_deduction_and_idempotent_rollback(self):
        ref = self.provider.deduct_stock("MED-0001", 3, "one")
        fresh = Provider(self.path)
        self.assertEqual(fresh.get_medicine("MED-0001")["quantity_in_stock"], 97)
        self.assertEqual(fresh.deduct_stock("MED-0001", 3, "one"), ref)
        rollback = fresh.restore_stock(ref)
        self.assertEqual(Provider(self.path).restore_stock(ref), rollback)
        self.assertEqual(fresh.get_medicine("MED-0001")["quantity_in_stock"], 100)

    def test_key_conflict_and_shortage_leave_stock_unchanged(self):
        self.provider.deduct_stock("MED-0001", 2, "one")
        with self.assertRaises(ValueError):
            self.provider.deduct_stock("MED-0001", 3, "one")
        with self.assertRaises(InsufficientStockError):
            self.provider.deduct_stock("MED-0001", 999)
        self.assertEqual(
            self.provider.get_medicine("MED-0001")["quantity_in_stock"], 98
        )

    def test_parallel_retry_deducts_once(self):
        def deduct(_):
            return Provider(self.path).deduct_stock("MED-0001", 2, "parallel")

        with ThreadPoolExecutor(4) as pool:
            refs = list(pool.map(deduct, range(4)))
        self.assertEqual(len(set(refs)), 1)
        self.assertEqual(
            self.provider.get_medicine("MED-0001")["quantity_in_stock"], 98
        )

    def test_workspace_failure_rolls_back_entire_delivery(self):
        with self.assertRaises(RuntimeError):
            with self.provider.workspace():
                self.provider._medicines[0]["quantity_in_stock"] += 30
                self.provider.restocks["r"] = {"status": "FULFILLED"}
                raise RuntimeError("simulated partial delivery")
        self.assertEqual(
            self.provider.get_medicine("MED-0001")["quantity_in_stock"], 100
        )
        self.assertNotIn("r", self.provider.restocks)

    def test_hard_process_restart_preserves_stock_and_request_fence(self):
        code = """
import os
from clinic.services.inventory import inventory_service as p
p.claim_request('scope','key','body')
p.deduct_stock('MED-0001', 4)
os._exit(0)
"""
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "INVENTORY_BACKEND": "durable_mock",
            "MOCK_INVENTORY_DB": str(self.path),
        }
        subprocess.run(
            [sys.executable, "-c", "import django; django.setup();\n" + code],
            env=env,
            check=True,
            cwd=Path(__file__).resolve().parents[2],
        )
        fresh = Provider(self.path)
        self.assertEqual(fresh.get_medicine("MED-0001")["quantity_in_stock"], 96)
        self.assertEqual(fresh.claim_request("scope", "key", "body"), "pending")
        with self.assertRaises(ValueError):
            fresh.claim_request("scope", "key", "different")


class ReplayRetentionTests(TestCase):
    def test_purge_keeps_tombstone_and_history(self):
        receipt = OperationReceipt.objects.create(
            scope="s",
            key="k",
            fingerprint="f",
            response={"medical": "synthetic"},
            status_code=201,
        )
        OperationReceipt.objects.filter(pk=receipt.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )
        call_command("purge_replay_bodies")
        receipt.refresh_from_db()
        self.assertIsNone(receipt.response)
        self.assertEqual(receipt.key, "k")
