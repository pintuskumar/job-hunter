"""Safe application smoke tests: isolated SQLite, no provider or email calls."""

import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ.update(
    {
        "APP_USERNAME": "test-admin",
        "APP_PASSWORD": "test-password",
        "REQUIRE_AUTH": "true",
        "DB_PATH": str(Path(_TEMP_DIR.name) / "test.db"),
        "ENABLE_SCHEDULER": "false",
        "RAPIDAPI_KEY": "",
        "HUNTER_API_KEY": "",
        "GOOGLE_SHEET_ID": "",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_SECURE": "false",
        "SMTP_STARTTLS": "true",
        "SMTP_USER": "test-user",
        "SMTP_PASS": "test-password",
        "SMTP_FROM_EMAIL": "sender@example.com",
    }
)

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


class ApplicationSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        token = base64.b64encode(b"test-admin:test-password").decode("ascii")
        cls.auth = {"Authorization": f"Basic {token}"}
        cls.client_context = TestClient(main.app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        _TEMP_DIR.cleanup()

    def test_health_is_public_and_ready(self):
        self.assertEqual(self.client.get("/health/live").json(), {"status": "ok"})
        ready = self.client.get("/health/ready")
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json(), {"status": "ready"})

    def test_private_routes_require_authentication(self):
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Basic", response.headers.get("www-authenticate", ""))

    def test_authenticated_reads_and_static_assets(self):
        stats = self.client.get("/api/stats", headers=self.auth)
        self.assertEqual(stats.status_code, 200)
        self.assertIn("total", stats.json())
        self.assertEqual(stats.headers.get("x-content-type-options"), "nosniff")

        marked = self.client.get("/api/jobs/marked", headers=self.auth)
        self.assertEqual(marked.status_code, 200)
        self.assertIn("jobs", marked.json())

        css = self.client.get("/static/style.css", headers=self.auth)
        self.assertEqual(css.status_code, 200)
        self.assertIn("text/css", css.headers.get("content-type", ""))

    @patch("main.sheets_credentials_available", return_value=True)
    def test_sheets_status_is_redacted(self, _available):
        with patch.object(main, "GOOGLE_SHEET_ID", "private-sheet-id"):
            response = self.client.get("/api/export/sheets/status", headers=self.auth)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "configured": True,
                "sheet_id_configured": True,
                "credentials_available": True,
            },
        )
        self.assertNotIn("private-sheet-id", response.text)

    @patch("main.verify_sheet_access")
    @patch("main.sheets_credentials_available", return_value=True)
    def test_sheets_verify_is_read_only_and_redacted(self, _available, verify):
        with patch.object(main, "GOOGLE_SHEET_ID", "private-sheet-id"):
            response = self.client.get("/api/export/sheets/verify", headers=self.auth)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"configured": True, "reachable": True})
        verify.assert_called_once_with(
            spreadsheet_id="private-sheet-id", creds_file=main.GOOGLE_SHEETS_CREDS
        )
        self.assertNotIn("private-sheet-id", response.text)

    def test_invalid_sheets_export_mode_is_rejected(self):
        response = self.client.post(
            "/api/export/sheets?mode=unexpected",
            headers=self.auth,
        )
        self.assertEqual(response.status_code, 422)

    def test_production_docs_are_disabled(self):
        self.assertEqual(self.client.get("/docs", headers=self.auth).status_code, 404)
        self.assertEqual(self.client.get("/openapi.json", headers=self.auth).status_code, 404)

    def test_cross_origin_writes_are_rejected_before_validation(self):
        response = self.client.post(
            "/api/profiles",
            headers={**self.auth, "Origin": "https://attacker.example"},
            json={},
        )
        self.assertEqual(response.status_code, 403)

        smtp_probe = self.client.post(
            "/api/email/test-connection",
            headers={**self.auth, "Origin": "https://attacker.example"},
        )
        self.assertEqual(smtp_probe.status_code, 403)

    def test_invalid_job_status_is_rejected(self):
        response = self.client.patch(
            "/api/jobs/nonexistent/status?status=unexpected",
            headers=self.auth,
        )
        self.assertEqual(response.status_code, 422)

    @patch("core.emailer._connect_smtp")
    def test_smtp_probe_authenticates_without_sending(self, connect):
        response = self.client.post(
            "/api/email/test-connection",
            headers=self.auth,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "transport": "starttls"})
        connect.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
