import os
from dotenv import load_dotenv

load_dotenv()

def getenv_list(name: str):
    raw = os.getenv(name, "") or ""
    # Allow comma or newline separated
    parts = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
    return parts

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Comma-separated @usernames or numeric IDs
SOURCE_CHANNELS = getenv_list("SOURCE_CHANNELS")  # e.g. @news1,@news2,-100123456789
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "")  # e.g. @my_channel or -100...
KEYWORDS = [k.lower() for k in getenv_list("KEYWORDS")]  # e.g. EV,전해액,동화

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "600"))
DB_PATH = os.getenv("DB_PATH", "/app/data/state.sqlite")

# Posting format
FORWARD_MODE = os.getenv("FORWARD_MODE", "forward")  # forward | copy
ADD_HEADER = os.getenv("ADD_HEADER", "true").lower() == "true"
