"""Google Sheets integration — push jobs to a sheet for n8n / outreach workflows."""

import json
from pathlib import Path

import google.auth
import gspread
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account

from config.settings import GOOGLE_SHEETS_CREDENTIALS_JSON
from core.database import get_jobs

WRITE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
READONLY_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Column headers that go into the sheet
HEADERS = [
    "Title", "Company", "Location", "India Friendly", "Location Note",
    "Relevance Score", "Tech Stack", "Experience Level", "Salary",
    "Job URL", "Source", "Posted Date", "Status", "Company Domain",
]


class SheetsConfigurationError(RuntimeError):
    """Raised when no usable Google Sheets credentials are configured."""


def _load_credentials(
    creds_file: str | None = None,
    credentials_json: str | None = None,
    scopes: list[str] | None = None,
):
    """Resolve Railway JSON, an explicit local file, or standard local ADC."""
    selected_scopes = scopes or WRITE_SCOPES
    raw_json = (
        GOOGLE_SHEETS_CREDENTIALS_JSON
        if credentials_json is None
        else credentials_json.strip()
    )

    if raw_json:
        try:
            info = json.loads(raw_json)
            if not isinstance(info, dict) or info.get("type") != "service_account":
                raise ValueError("expected service_account credentials")
            return service_account.Credentials.from_service_account_info(
                info, scopes=selected_scopes
            )
        except (KeyError, TypeError, ValueError, DefaultCredentialsError) as exc:
            raise SheetsConfigurationError(
                "Google Sheets service-account credentials are invalid"
            ) from exc

    if creds_file:
        path = Path(creds_file).expanduser()
        if not path.is_file():
            raise SheetsConfigurationError(
                "Google Sheets credentials are not configured"
            )
        try:
            return service_account.Credentials.from_service_account_file(
                str(path), scopes=selected_scopes
            )
        except (KeyError, TypeError, ValueError, DefaultCredentialsError) as exc:
            raise SheetsConfigurationError(
                "Google Sheets service-account credentials are invalid"
            ) from exc

    try:
        credentials, _ = google.auth.default(scopes=selected_scopes)
        return credentials
    except DefaultCredentialsError as exc:
        raise SheetsConfigurationError(
            "Google Sheets credentials are not configured"
        ) from exc


def _get_client(
    creds_file: str | None = None,
    credentials_json: str | None = None,
    scopes: list[str] | None = None,
) -> gspread.Client:
    credentials = _load_credentials(
        creds_file=creds_file,
        credentials_json=credentials_json,
        scopes=scopes,
    )
    return gspread.authorize(credentials)


def sheets_credentials_available(
    creds_file: str | None = None,
    credentials_json: str | None = None,
) -> bool:
    """Check credential availability without refreshing a token or calling Sheets."""
    try:
        _load_credentials(
            creds_file=creds_file,
            credentials_json=credentials_json,
            scopes=READONLY_SCOPES,
        )
        return True
    except SheetsConfigurationError:
        return False


def verify_sheet_access(
    spreadsheet_id: str,
    creds_file: str | None = None,
    credentials_json: str | None = None,
) -> None:
    """Perform a read-only metadata request against the configured spreadsheet."""
    client = _get_client(
        creds_file=creds_file,
        credentials_json=credentials_json,
        scopes=READONLY_SCOPES,
    )
    client.open_by_key(spreadsheet_id)


def _job_to_row(job: dict) -> list:
    return [
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("india_friendly", "unknown"),
        job.get("location_note", ""),
        job.get("relevance_score", 0),
        job.get("tech_stack", ""),
        job.get("experience_level", ""),
        job.get("salary", ""),
        job.get("url", ""),
        job.get("source", ""),
        job.get("posted_date", ""),
        job.get("status", "new"),
        job.get("company_domain", ""),
    ]


def export_to_sheet(
    creds_file: str | None,
    spreadsheet_id: str,
    sheet_name: str = "Jobs",
    min_score: int = 0,
    india_friendly: str = None,
    source: str = None,
    search: str = None,
    tech: str = None,
    mode: str = "replace",
) -> dict:
    """
    Export filtered jobs to a Google Sheet.

    Args:
        creds_file: path to service account JSON
        spreadsheet_id: the Google Sheet ID (from the URL)
        sheet_name: worksheet tab name
        min_score: minimum relevance score
        india_friendly: 'yes', 'maybe', 'no', or None
        source: filter by source
        search: search query
        tech: tech filter
        mode: 'replace' (clear + rewrite) or 'append' (add new rows)

    Returns:
        dict with export stats
    """
    if mode not in {"replace", "append"}:
        raise ValueError("mode must be replace or append")

    client = _get_client(creds_file=creds_file, scopes=WRITE_SCOPES)
    spreadsheet = client.open_by_key(spreadsheet_id)

    # Get or create worksheet
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(HEADERS))

    # Fetch jobs from DB with filters
    jobs = get_jobs(
        min_score=min_score,
        india_friendly=india_friendly,
        source=source,
        search=search,
        tech=tech,
        limit=500,
    )

    rows = [_job_to_row(j) for j in jobs]

    if mode == "replace":
        worksheet.clear()
        worksheet.update(values=[HEADERS] + rows, range_name="A1", raw=True)
    else:
        # Append mode — check if headers exist
        existing = worksheet.get_all_values()
        if not existing:
            worksheet.update(values=[HEADERS], range_name="A1", raw=True)
        if rows:
            # Remote job fields are untrusted. RAW prevents formula execution.
            worksheet.append_rows(rows, value_input_option="RAW")

    # Auto-format header row bold
    worksheet.format("A1:N1", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.15, "green": 0.15, "blue": 0.2},
    })

    return {
        "exported": len(rows),
        "sheet_name": sheet_name,
        "mode": mode,
    }
