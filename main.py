
import os, asyncio, re, time, logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import tldextract

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("forwarder")

API_ID = int(os.getenv("API_ID","0"))
API_HASH = os.getenv("API_HASH","")
STRING = os.getenv("TELEGRAM_STRING_SESSION","")
TARGET_CHAT = os.getenv("TARGET_CHAT","")
CHANNELS_RAW = os.getenv("CHANNELS","")
MAX_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE","30") or "30")
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS","12") or "12")
POST_MODE = os.getenv("POST_MODE","simple").lower()
DRY_RUN = os.getenv("DRY_RUN","0") == "1"

if not (API_ID and API_HASH and STRING and TARGET_CHAT and CHANNELS_RAW):
    log.error("Missing required env vars. Need API_ID, API_HASH, TELEGRAM_STRING_SESSION, TARGET_CHAT, CHANNELS")
    raise SystemExit(1)

def parse_channels(s: str):
    # split by newline or comma; allow comma+space or bare commas
    parts = []
    for line in s.replace("\r","").split("\n"):
        if not line.strip():
            continue
        parts.extend([p.strip() for p in line.split(",") if p.strip()])
    # keep only t.me urls
    urls = []
    for p in parts:
        if p.startswith("http"):
            u = urlparse(p)
            if u.netloc.lower() in ("t.me","telegram.me"):
                urls.append(p)
        # ignore @name entries
    return urls

SOURCES = parse_channels(CHANNELS_RAW)
if not SOURCES:
    log.error("No valid t.me URLs in CHANNELS.")
    raise SystemExit(1)

def extract_urls(text: str):
    if not text: 
        return []
    # simple URL regex
    pattern = re.compile(r'(https?://[^\s]+)', re.IGNORECASE)
    urls = pattern.findall(text)
    # normalize by removing trailing punctuation
    cleaned = []
    for u in urls:
        u = u.rstrip(").,]}'\">")
        cleaned.append(u)
    return cleaned

def short_host(u: str):
    try:
        ex = tldextract.extract(u)
        return ".".join([p for p in [ex.domain, ex.suffix] if p])
    except Exception:
        return urlparse(u).netloc

async def run():
    client = TelegramClient(StringSession(STRING), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        log.error("StringSession not authorized. Re-create TELEGRAM_STRING_SESSION locally.")
        return

    # resolve target
    target = TARGET_CHAT
    try:
        target_entity = await client.get_entity(target)
    except Exception as e:
        log.error(f"Failed to resolve TARGET_CHAT={target}: {e}")
        return

    lookback = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    posted_count = 0
    for src in SOURCES:
        # convert t.me/url -> username
        path = urlparse(src).path.strip("/")
        if not path:
            log.warning(f"Skip: bad url path {src}")
            continue
        username = path.split("/")[0]
        try:
            entity = await client.get_entity(username)
        except Exception as e:
            log.warning(f"Skip source {src}: {e}")
            continue

        log.info(f"Fetching from {src} (<= {MAX_PER_SOURCE} msgs, since {lookback.isoformat()})")
        # fetch messages
        offset_id = 0
        collected = 0
        while collected < MAX_PER_SOURCE:
            hist = await client(GetHistoryRequest(
                peer=entity, limit=min(100, MAX_PER_SOURCE-collected),
                offset_date=None, offset_id=offset_id, max_id=0, min_id=0, add_offset=0, hash=0
            ))
            msgs = hist.messages
            if not msgs: break
            for m in msgs:
                offset_id = m.id
                collected += 1
                if getattr(m, "date", lookback) < lookback:
                    continue
                # build permalink
                permalink = f"https://t.me/{username}/{m.id}"
                text = (m.message or "").strip()
                urls = extract_urls(text)

                if urls:
                    for u in urls:
                        host = short_host(u)
                        if POST_MODE == "compact":
                            out = f"{host} → {u}\n{permalink}"
                        else:
                            out = f"[{host}] {u}\n원문: {permalink}"
                        if DRY_RUN:
                            log.info(f"DRY_POST:\n{out}")
                        else:
                            try:
                                await client.send_message(target_entity, out, link_preview=False)
                                posted_count += 1
                            except Exception as e:
                                log.warning(f"Post failed: {e}")
                else:
                    # no URLs; send trimmed text + permalink
                    head = (text[:120] + ("…" if len(text) > 120 else "")) if text else "(미리보기 없음)"
                    out = f"{head}\n원문: {permalink}"
                    if DRY_RUN:
                        log.info(f"DRY_POST:\n{out}")
                    else:
                        try:
                            await client.send_message(target_entity, out, link_preview=False)
                            posted_count += 1
                        except Exception as e:
                            log.warning(f"Post failed: {e}")
            if len(msgs) < 100: break

    log.info(f"Done. Posted {posted_count} messages (mode={POST_MODE}, dry={DRY_RUN}).")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run())
