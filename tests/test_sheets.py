"""Offline unit tests for Google Sheets credential and export behavior."""

import unittest
from unittest.mock import MagicMock, patch

from google.auth.exceptions import DefaultCredentialsError

from core import sheets


class SheetsCredentialTests(unittest.TestCase):
    def test_json_secret_has_precedence_over_adc(self):
        credential = object()
        raw = '{"type":"service_account"}'
        with (
            patch.object(
                sheets.service_account.Credentials,
                "from_service_account_info",
                return_value=credential,
            ) as from_info,
            patch.object(sheets.google.auth, "default") as default,
        ):
            resolved = sheets._load_credentials(credentials_json=raw)

        self.assertIs(resolved, credential)
        from_info.assert_called_once_with(
            {"type": "service_account"}, scopes=sheets.WRITE_SCOPES
        )
        default.assert_not_called()

    def test_invalid_json_fails_closed_without_adc_fallback(self):
        with (
            patch.object(sheets.google.auth, "default") as default,
            self.assertRaises(sheets.SheetsConfigurationError),
        ):
            sheets._load_credentials(credentials_json="not-json")
        default.assert_not_called()

    def test_malformed_service_account_is_redacted(self):
        with (
            patch.object(
                sheets.service_account.Credentials,
                "from_service_account_info",
                side_effect=DefaultCredentialsError("private parse details"),
            ),
            self.assertRaisesRegex(
                sheets.SheetsConfigurationError,
                "Google Sheets service-account credentials are invalid",
            ),
        ):
            sheets._load_credentials(credentials_json='{"type":"service_account"}')

    def test_missing_secret_and_file_use_readonly_adc(self):
        credential = object()
        with patch.object(
            sheets.google.auth,
            "default",
            return_value=(credential, "example-project"),
        ) as default:
            resolved = sheets._load_credentials(
                creds_file="", credentials_json="", scopes=sheets.READONLY_SCOPES
            )

        self.assertIs(resolved, credential)
        default.assert_called_once_with(scopes=sheets.READONLY_SCOPES)

    def test_explicit_missing_file_fails_without_adc_fallback(self):
        with (
            patch.object(sheets.google.auth, "default") as default,
            self.assertRaises(sheets.SheetsConfigurationError),
        ):
            sheets._load_credentials(
                creds_file="missing-service-account.json", credentials_json=""
            )
        default.assert_not_called()


class SheetsExportTests(unittest.TestCase):
    @patch("core.sheets.get_jobs", return_value=[])
    @patch("core.sheets._get_client")
    def test_replace_export_writes_headers_and_redacts_sheet_id(self, get_client, get_jobs):
        worksheet = MagicMock()
        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        get_client.return_value.open_by_key.return_value = spreadsheet

        result = sheets.export_to_sheet(
            creds_file=None,
            spreadsheet_id="private-sheet-id",
            sheet_name="Smoke",
            source="__empty_smoke__",
            mode="replace",
        )

        self.assertEqual(result, {"exported": 0, "sheet_name": "Smoke", "mode": "replace"})
        self.assertNotIn("spreadsheet_id", result)
        worksheet.clear.assert_called_once_with()
        worksheet.update.assert_called_once_with(
            values=[sheets.HEADERS], range_name="A1", raw=True
        )
        worksheet.format.assert_called_once()
        get_jobs.assert_called_once()

    def test_invalid_mode_is_rejected_before_google_access(self):
        with patch("core.sheets._get_client") as get_client:
            with self.assertRaises(ValueError):
                sheets.export_to_sheet(None, "sheet-id", mode="unexpected")
        get_client.assert_not_called()

    @patch("core.sheets._get_client")
    def test_readonly_verifier_only_opens_sheet(self, get_client):
        client = get_client.return_value
        sheets.verify_sheet_access("sheet-id", credentials_json="ignored")

        get_client.assert_called_once_with(
            creds_file=None,
            credentials_json="ignored",
            scopes=sheets.READONLY_SCOPES,
        )
        client.open_by_key.assert_called_once_with("sheet-id")

    @patch("core.sheets.get_jobs", return_value=[{"title": "=1+1"}])
    @patch("core.sheets._get_client")
    def test_append_writes_untrusted_values_as_raw_text(self, get_client, _get_jobs):
        worksheet = MagicMock()
        worksheet.get_all_values.return_value = [sheets.HEADERS]
        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        get_client.return_value.open_by_key.return_value = spreadsheet

        sheets.export_to_sheet(None, "sheet-id", mode="append")

        rows = worksheet.append_rows.call_args.args[0]
        self.assertEqual(rows[0][0], "=1+1")
        self.assertEqual(
            worksheet.append_rows.call_args.kwargs["value_input_option"], "RAW"
        )


if __name__ == "__main__":
    unittest.main()
