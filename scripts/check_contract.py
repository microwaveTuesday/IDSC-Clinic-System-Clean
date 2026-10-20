"""Compare committed and runtime OpenAPI structurally, ignoring YAML ordering."""

import subprocess
import sys
import tempfile
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    dynamic = Path(directory) / "dynamic.yaml"
    subprocess.run(
        [
            sys.executable,
            str(root / "backend/manage.py"),
            "spectacular",
            "--validate",
            "--fail-on-warn",
            "--file",
            str(dynamic),
        ],
        check=True,
    )
    expected = yaml.safe_load((root / "openapi.yaml").read_text(encoding="utf-8"))
    actual = yaml.safe_load(dynamic.read_text(encoding="utf-8"))
    assert (
        expected == actual
    ), "Committed OpenAPI differs from runtime; regenerate and review."
    paths = actual["paths"]
    count = sum(
        method in ("get", "post", "put", "patch", "delete", "head", "options", "trace")
        for item in paths.values()
        for method in item
    )
    print(
        f"PASS: static/runtime contract equality; {len(paths)} paths, {count} operations."
    )
