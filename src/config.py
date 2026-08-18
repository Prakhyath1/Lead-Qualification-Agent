import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Key validation
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Supported models with prioritized fallback chain
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "groq/compound",
]

# Scoring Thresholds
HOT_THRESHOLD = 80
WARM_THRESHOLD = 50

# Score Maximums
MAX_FIT_SCORE = 50
MAX_INTENT_SCORE = 50
MAX_TOTAL_SCORE = 100

# Sub-score Maximums for Fit (Total = 50)
FIT_COMPANY_SIZE_MAX = 15
FIT_SENIORITY_MAX = 20
FIT_INDUSTRY_MAX = 15

# Sub-score Maximums for Intent (Total = 50)
INTENT_BEHAVIOR_MAX = 25
INTENT_URGENCY_MAX = 15
INTENT_BUDGET_MAX = 10

# Paths
DEFAULT_INPUT_FILE = BASE_DIR / "data" / "leads.json"
DEFAULT_CSV_INPUT_FILE = BASE_DIR / "data" / "leads.csv"
DEFAULT_EMAILS_FILE = BASE_DIR / "data" / "inbound_emails.json"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_OUTPUT_JSON = DEFAULT_OUTPUT_DIR / "ranked_leads.json"
DEFAULT_OUTPUT_CSV = DEFAULT_OUTPUT_DIR / "ranked_leads.csv"
DEFAULT_OUTPUT_REPORT = DEFAULT_OUTPUT_DIR / "qualification_report.md"
SCORING_LOGIC_FILE = BASE_DIR / "SCORING_LOGIC.md"


def validate_api_key() -> str:
    """Validates and returns the GROQ API key, or exits gracefully with instructions."""
    key = os.getenv("GROQ_API_KEY")
    if not key or key.strip() in ("", "your_api_key_here", "your_groq_api_key_here"):
        print("\n[ERROR] GROQ_API_KEY not configured in .env file.")
        print("Please obtain a free API key at https://console.groq.com/keys")
        print("and add it to your .env file: GROQ_API_KEY=gsk_...\n")
        sys.exit(1)
    return key.strip()
