import os
from pydantic import BaseModel

def _get_keywords():
    k1 = os.getenv("KEYWORDS", "")
    return k1 if k1.strip() else os.getenv("INTEREST_KEYWORDS", "")

def _get_channels():
    s = os.getenv("SRC_CHANNELS", "")
    if not s.strip():
        s = os.getenv("SOURCE_CHANNELS", "")
    return s

def _get_api_id():
    val = os.getenv("TELEGRAM_API_ID", "") or os.getenv("API_ID", "") or "0"
    return int(val)

def _get_api_hash():
    return os.getenv("TELEGRAM_API_HASH", "") or os.getenv("API_HASH", "")

def _get_interval_min():
    # Prefer RUN_INTERVAL_MIN in minutes; if POLL_INTERVAL (seconds) is provided, convert to minutes
    rim = os.getenv("RUN_INTERVAL_MIN", "").strip()
    if rim:
        try:
            return max(1, int(rim))
        except:
            pass
    poll = os.getenv("POLL_INTERVAL", "").strip()
    if poll:
        try:
            return max(1, int(int(poll) / 60))
        except:
            pass
    return 30

class Settings(BaseModel):
    TELEGRAM_API_ID: int = _get_api_id()
    TELEGRAM_API_HASH: str = _get_api_hash()
    TELETHON_SESSION: str = os.getenv("TELETHON_SESSION", "")
    SRC_CHANNELS: str = _get_channels()
    KEYWORDS: str = _get_keywords()
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./newsbot.db")
    RUN_INTERVAL_MIN: int = _get_interval_min()
    MAX_DAYS_KEEP: int = int(os.getenv("MAX_DAYS_KEEP", "60"))
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    TARGET_CHANNEL: str = os.getenv("TARGET_CHANNEL", "") or os.getenv("TARGET_CHAT_ID","")

settings = Settings()
