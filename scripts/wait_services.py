"""Portable readiness check; bounded retries, no credentials in diagnostics."""

import time
from urllib.request import urlopen

for url in ("http://127.0.0.1:8002/api/auth/setup/", "http://127.0.0.1:5173"):
    for attempt in range(60):
        try:
            with urlopen(url, timeout=2) as response:
                assert response.status == 200
            break
        except Exception:
            if attempt == 59:
                raise SystemExit(f"Service failed readiness: {url}")
            time.sleep(1)
print("Backend and frontend ready.")
