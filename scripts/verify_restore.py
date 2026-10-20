"""Disposable physical backup/restore exercise, SQLite or PostgreSQL.

No backups or row contents leave the temporary directory. PostgreSQL requires
pg_dump/pg_restore matching the server major version and CREATEDB privileges.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

if os.environ.get("CLINIC_DISPOSABLE") != "1":
    raise SystemExit("Refusing: set CLINIC_DISPOSABLE=1; use synthetic data only.")
root = Path(__file__).resolve().parents[1]
(root / ".runtime").mkdir(exist_ok=True)
postgres = "postgresql" in os.environ.get("DB_ENGINE", "")
suffix = uuid4().hex[:10]
source, target = f"verification_source_{suffix}", f"verification_restore_{suffix}"


def run(args, env):
    subprocess.run([sys.executable, *args], cwd=root, env=env, check=True)


with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    env = {
        **os.environ,
        "CLINIC_DATA_BACKEND": "database",
        "INVENTORY_BACKEND": "durable_mock",
        "MOCK_INVENTORY_DB": str(path / "mock-inventory.sqlite3"),
        "CLINIC_EMPTY_START": "0",
    }
    admin = None
    try:
        if postgres:
            import psycopg
            from psycopg import sql

            admin = psycopg.connect(
                dbname=os.environ.get("DB_NAME", "postgres"),
                user=os.environ["DB_USER"],
                password=os.environ.get("DB_PASSWORD", ""),
                host=os.environ.get("DB_HOST", "127.0.0.1"),
                port=os.environ.get("DB_PORT", "5432"),
                autocommit=True,
            )
            for name in (source, target):
                admin.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name))
                )
            env["DB_NAME"] = source
        else:
            env["DB_NAME"] = str(path / "source.sqlite3")
        run(["backend/manage.py", "migrate", "--noinput"], env)
        run(["scripts/verify_persistence.py", "write"], env)
        if postgres:
            pg_env = {**env, "PGPASSWORD": env.get("DB_PASSWORD", "")}
            common = [
                "-h",
                env.get("DB_HOST", "127.0.0.1"),
                "-p",
                env.get("DB_PORT", "5432"),
                "-U",
                env["DB_USER"],
            ]
            subprocess.run(
                ["pg_dump", *common, "-Fc", "-f", str(path / "clinic.dump"), source],
                env=pg_env,
                check=True,
            )
            subprocess.run(
                [
                    "pg_restore",
                    *common,
                    "--no-owner",
                    "--exit-on-error",
                    "-d",
                    target,
                    str(path / "clinic.dump"),
                ],
                env=pg_env,
                check=True,
            )
            env["DB_NAME"] = target
        else:
            from contextlib import closing

            with closing(sqlite3.connect(env["DB_NAME"])) as src, closing(
                sqlite3.connect(path / "restored.sqlite3")
            ) as dst:
                src.backup(dst)
            env["DB_NAME"] = str(path / "restored.sqlite3")
        # Back up the separately owned mock ledger with all application writes stopped.
        from contextlib import closing

        with closing(sqlite3.connect(env["MOCK_INVENTORY_DB"])) as src, closing(
            sqlite3.connect(path / "restored-inventory.sqlite3")
        ) as dst:
            src.backup(dst)
        env["MOCK_INVENTORY_DB"] = str(path / "restored-inventory.sqlite3")
        run(["backend/manage.py", "migrate", "--check"], env)
        run(["backend/manage.py", "check"], env)
        run(["scripts/verify_persistence.py", "read"], env)
        code = """
import django; django.setup()
from django.db import IntegrityError, transaction
from clinic.models import MedicineDispensation
from clinic.services.clinic import clinic_service
from clinic.services.inventory import inventory_service
row = MedicineDispensation.objects.get()
assert inventory_service.get_medicine('MED-0001')['quantity_in_stock'] == 99
assert row.inventory_transaction_id in inventory_service._transactions
assert clinic_service.repository.get_dispensation(row.pk)['quantity'] == 1
try:
    with transaction.atomic():
        MedicineDispensation.objects.create(student_id='synthetic', medicine_id='MED-0001', quantity=0)
except IntegrityError:
    pass
else:
    raise AssertionError('Restored constraint missing')
ref = inventory_service.restore_stock(row.inventory_transaction_id)
assert inventory_service.restore_stock(row.inventory_transaction_id) == ref
assert inventory_service.get_medicine('MED-0001')['quantity_in_stock'] == 100
print('PASS: restored application access, Inventory reference/stock, rollback and quantity constraint.')
"""
        subprocess.run(
            [sys.executable, "-c", code],
            cwd=root / "backend",
            env={**env, "DJANGO_SETTINGS_MODULE": "config.settings"},
            check=True,
        )
        print(
            "PASS: physical backup/restore exercise:",
            "PostgreSQL" if postgres else "SQLite",
        )
    finally:
        if admin:
            for name in (source, target):
                admin.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                        sql.Identifier(name)
                    )
                )
            admin.close()
