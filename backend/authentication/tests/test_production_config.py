import os, subprocess, sys
from pathlib import Path
from django.test import SimpleTestCase


class ProductionConfigurationTests(SimpleTestCase):
    def run_config(self, **overrides):
        env = os.environ.copy()
        env.update({"DEBUG": "False", "ALLOWED_HOSTS": "clinic.school.test"})
        env.pop("SECRET_KEY", None)
        env.update(overrides)
        return subprocess.run(
            [sys.executable, "manage.py", "check", "--deploy"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_missing_secret_fails_closed(self):
        result = self.run_config()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("private SECRET_KEY", result.stderr)

    def test_valid_explicit_production_configuration(self):
        result = self.run_config(SECRET_KEY="private-validation-only-" + ("x" * 64))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("security.W", result.stderr)

    def test_wildcard_hosts_fail_closed(self):
        result = self.run_config(
            SECRET_KEY="private-validation-only-" + ("x" * 64), ALLOWED_HOSTS="*"
        )
        self.assertNotEqual(result.returncode, 0)
