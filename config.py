"""
Configuration settings for WhatsApp Web Scraper and Google Sheets Bot.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "tx_images"
CROPS_DIR = DATA_DIR / "crops"

DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
CROPS_DIR.mkdir(exist_ok=True)

# Kimi WebBridge Settings
WEBBRIDGE_DAEMON_URL = os.getenv("WEBBRIDGE_URL", "http://127.0.0.1:10086/command")
WEBBRIDGE_STATUS_URL = os.getenv("WEBBRIDGE_STATUS_URL", "http://127.0.0.1:10086/status")
SESSION_NAME = "whatsapp-track"
WHATSAPP_WEB_URL = "https://web.whatsapp.com/"

# Google Sheets Configuration
DEFAULT_CREDS_PATH = os.path.expanduser(r"~\Downloads\ledgerweb-acaf45d521cb.json")
GOOGLE_CREDS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", DEFAULT_CREDS_PATH)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1nhGx50fEs2-lLhMsZbbjJuR8lpIBieIF88kPWxWxv_c")
SPREADSHEET_NAME = "HISSAB KITAB "
WORKSHEET_NAME = "Sheet1"

# Service Account Email for verification
SERVICE_ACCOUNT_EMAIL = "ledger-bot@ledgerweb.iam.gserviceaccount.com"

# Checkpoint UTR
DEFAULT_CHECKPOINT_UTR = "662590373713"
