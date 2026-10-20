"""Export counts only; never upload raw medical/API responses or credentials."""

import json
import os
import re
from pathlib import Path

source = Path(os.environ["RUNNER_TEMP"]) / "backend-tests.txt"
text = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
ran = re.search(r"Ran (\d+) tests? in ([\d.]+)s", text)
skips = re.search(r"OK \(skipped=(\d+)\)", text)
result = {
    "revision": os.environ.get("GITHUB_SHA"),
    "database": os.environ.get("SUMMARY_DATABASE"),
    "tests": int(ran[1]) if ran else None,
    "seconds": float(ran[2]) if ran else None,
    "skipped": int(skips[1]) if skips else 0,
    "suite_passed": bool(
        re.search(r"^OK(?: \(skipped=\d+\))?\s*$", text, re.MULTILINE)
    ),
    "job_status": os.environ.get("SUMMARY_STATUS"),
}
Path("quality-summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result))
