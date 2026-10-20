"""HTTPS smoke using the supplied private CA, synthetic first Owner and real proxy."""

import http.cookiejar
import json
import os
import ssl
import sys
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, HTTPSHandler, Request

if os.environ.get("CLINIC_DISPOSABLE") != "1":
    raise SystemExit("Disposable environments only.")
context = ssl.create_default_context(cafile=os.environ["CLINIC_CA_FILE"])
opener = build_opener(
    HTTPCookieProcessor(http.cookiejar.CookieJar()), HTTPSHandler(context=context)
)
base = "https://localhost"


def call(path, data=None, key=None):
    headers = {"Accept": "application/json"}
    if data is not None:
        token = call("/api/auth/csrf/")["csrfToken"]
        headers.update(
            {
                "Content-Type": "application/json",
                "Origin": base,
                "Referer": base + "/",
                "X-CSRFToken": token,
            }
        )
        if key:
            headers["Idempotency-Key"] = key
    with opener.open(
        Request(
            base + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers=headers,
        ),
        timeout=30,
    ) as response:
        return json.load(response)


credentials = {
    "username": os.environ["CLINIC_TEST_USERNAME"],
    "password": os.environ["CLINIC_TEST_PASSWORD"],
}
manifest = Path(os.environ["RUNNER_TEMP"]) / "deployment-manifest.json"
if sys.argv[1] == "write":
    assert call("/api/auth/setup/")["owner_registration_available"]
    call(
        "/api/auth/owner/register/",
        {**credentials, "confirm_password": credentials["password"]},
    )
    assert call("/api/auth/me/")["role"] == "OWNER"
    call("/api/v1/dashboard/")
    health = call(
        "/api/v1/health-records/",
        {"student_id": "2026-0001", "allergies": "synthetic deployment smoke"},
        "deployment-health",
    )
    dispense = call(
        "/api/v1/medicine-dispensations/",
        {
            "student_id": "2026-0001",
            "medicine_id": "MED-0001",
            "quantity": 1,
            "reason": "synthetic deployment smoke",
        },
        "deployment-dispense",
    )
    manifest.write_text(
        json.dumps(
            {
                "health": health["health_record_id"],
                "dispensation": dispense["dispensation_id"],
                "reference": dispense["inventory_transaction_id"],
            }
        ),
        encoding="utf-8",
    )
    print(
        "PASS: trusted HTTPS proxy, secure session/CSRF, Owner setup, dashboard, persistent record and dispense."
    )
else:
    call("/api/auth/login/", credentials)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert (
        call(f"/api/v1/health-records/{data['health']}/")["allergies"]
        == "synthetic deployment smoke"
    )
    row = call(f"/api/v1/medicine-dispensations/{data['dispensation']}/")
    assert row["inventory_transaction_id"] == data["reference"]
    assert call("/api/v1/medicines/MED-0001/")["quantity_in_stock"] == 99
    rollback = call(
        f"/api/v1/medicine-dispensations/{data['dispensation']}/rollback/",
        {},
        "deployment-rollback",
    )
    assert rollback["status"] == "ROLLED_BACK"
    assert call("/api/v1/medicines/MED-0001/")["quantity_in_stock"] == 100
    print(
        "PASS: deployed backend restart retained Clinic rows and mock stock/reference; rollback restores stock once."
    )
