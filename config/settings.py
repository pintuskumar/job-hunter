import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a conventional boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    """Parse and range-check an integer environment variable."""
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


BASE_DIR = Path(__file__).resolve().parent.parent

# Database
_volume_root = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_default_db_path = Path(_volume_root) / "jobs.db" if _volume_root else BASE_DIR / "jobs.db"
_configured_db_path = Path(os.getenv("DB_PATH", str(_default_db_path))).expanduser()
if not _configured_db_path.is_absolute():
    _configured_db_path = BASE_DIR / _configured_db_path
DB_PATH = str(_configured_db_path.resolve())

# API Keys (optional for test version)
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
JSEARCH_MONTHLY_LIMIT = _env_int("JSEARCH_MONTHLY_LIMIT", 200, 1, 100000)
JSEARCH_MONTHLY_RESERVE = _env_int("JSEARCH_MONTHLY_RESERVE", 20, 0, 99999)
if JSEARCH_MONTHLY_RESERVE >= JSEARCH_MONTHLY_LIMIT:
    raise RuntimeError("JSEARCH_MONTHLY_RESERVE must be lower than JSEARCH_MONTHLY_LIMIT")

# Email settings. SMTP_* is the canonical contract; the older Gmail-specific
# names remain supported so existing local installations keep working.
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = _env_int("SMTP_PORT", 465, 1, 65535)
SMTP_SECURE = _env_bool("SMTP_SECURE", True)
SMTP_STARTTLS = _env_bool("SMTP_STARTTLS", not SMTP_SECURE)
if not SMTP_SECURE and not SMTP_STARTTLS:
    raise RuntimeError("SMTP_STARTTLS must be enabled when SMTP_SECURE is false")
SMTP_USER = (os.getenv("SMTP_USER") or os.getenv("SENDER_EMAIL", "")).strip()
SMTP_PASS = os.getenv("SMTP_PASS") or os.getenv("SENDER_APP_PASSWORD", "")
SMTP_FROM_EMAIL = (
    os.getenv("SMTP_FROM_EMAIL") or os.getenv("SENDER_EMAIL") or SMTP_USER
).strip()

# Backwards-compatible exports used by older modules and integrations.
SENDER_EMAIL = SMTP_FROM_EMAIL
SENDER_APP_PASSWORD = SMTP_PASS
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")
EMAIL_CONFIGURED = bool(SMTP_HOST and SMTP_USER and SMTP_PASS and SMTP_FROM_EMAIL)

# Daily digest scheduler
ENABLE_SCHEDULER = _env_bool("ENABLE_SCHEDULER", False)
DAILY_EMAIL_HOUR = _env_int("DAILY_EMAIL_HOUR", 9, 0, 23)
DAILY_EMAIL_TIMEZONE = os.getenv("DAILY_EMAIL_TIMEZONE", "Asia/Kolkata").strip()
DAILY_JOBS_COUNT = _env_int("DAILY_JOBS_COUNT", 15, 1, 100)

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "").strip()
GOOGLE_SHEETS_CREDS = os.getenv("GOOGLE_SHEETS_CREDS", "").strip()
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()

# Search criteria defaults
DEFAULT_SEARCH_TERMS = [
    "backend developer python",
    "python django developer",
    "fastapi developer",
    "backend engineer python",
    "python developer",
]

RELEVANT_TECH = [
    "python", "django", "fastapi", "flask", "celery", "redis",
    "postgresql", "postgres", "mysql", "mongodb", "docker",
    "kubernetes", "aws", "gcp", "rest", "graphql", "node",
    "nodejs", "express", "sql", "nosql", "microservices",
    "rabbitmq", "kafka", "elasticsearch",
]

TITLE_KEYWORDS_POSITIVE = [
    "backend", "back-end", "back end", "python", "django",
    "fastapi", "software engineer", "software developer",
    "full stack", "fullstack", "full-stack", "api developer",
]

TITLE_KEYWORDS_NEGATIVE = [
    "frontend", "front-end", "front end", "ios", "android",
    "mobile", "devops", "data scientist", "machine learning",
    "ml engineer", "ui/ux", "designer", "qa", "test",
    "intern", "internship", "trainee", "junior",
]

# ── Location / India Remote Filtering ──

# Keywords that CONFIRM India/Asia people can apply
LOCATION_INDIA_POSITIVE = [
    "india", "asia", "worldwide", "global", "anywhere",
    "apac", "asia pacific", "asia-pacific",
    "remote - global", "remote global", "globally distributed",
    "work from anywhere", "location independent",
    "south asia", "southeast asia", "emea/apac",
    "mumbai", "bangalore", "bengaluru", "hyderabad", "pune",
    "delhi", "chennai", "kolkata", "noida", "gurgaon", "gurugram",
    "new delhi", "kochi", "jaipur", "ahmedabad", "remote - india",
    "ist", "indian standard time",
]

# Keywords that BLOCK India — these mean US/EU only
LOCATION_INDIA_NEGATIVE = [
    "us only", "usa only", "us-only", "united states only",
    "must be located in the us", "must reside in the us",
    "us-based", "us based", "u.s. only", "u.s. based",
    "canada only", "uk only", "eu only", "europe only",
    "european union only", "uk-based", "eu-based",
    "must be authorized to work in the united states",
    "no visa sponsorship", "us citizen", "us work authorization",
    "est/cst/pst", "americas only", "americas timezone",
    "north america only", "na only", "latam only",
]

# Timezone overlap hints — India (IST = UTC+5:30)
# These timezones have reasonable overlap with IST
TIMEZONE_COMPATIBLE = [
    "ist", "gmt", "utc", "cet", "eet", "ast",
    "flexible", "async", "asynchronous",
    "overlap", "any timezone", "all timezones",
]

TIMEZONE_INCOMPATIBLE = [
    "pst only", "est only", "cst only", "mst only",
    "pacific time only", "eastern time only",
    "us timezone required", "us hours required",
    "core hours pst", "core hours est",
]

# Minimum relevance score to show in polished results
MIN_RELEVANCE_SCORE = 50

# Server and optional HTTP Basic authentication. Health checks intentionally
# remain public; all other routes are protected when APP_PASSWORD is set.
HOST = os.getenv("HOST", "127.0.0.1").strip()
PORT = _env_int("PORT", 8000, 1, 65535)
RELOAD = _env_bool("RELOAD", False)
APP_USERNAME = os.getenv("APP_USERNAME", "jobhunter").strip() or "jobhunter"
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
REQUIRE_AUTH = _env_bool("REQUIRE_AUTH", False)
if REQUIRE_AUTH and not APP_PASSWORD:
    raise RuntimeError("APP_PASSWORD is required when REQUIRE_AUTH is true")

# Extra origins (e.g. the Vercel-hosted frontend) allowed to call the API
# cross-origin, for both CORS headers and the same-origin mutation guard.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
