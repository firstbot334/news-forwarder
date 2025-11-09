import asyncio, logging, re, urllib.parse, httpx
from bs4 import BeautifulSoup
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from sqlalchemy import create_engine, insert, MetaData, Table, Column, Integer, String, Text, DateTime, func
from src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("collector")
URL_RX = re.compile(r"(https?://\S+)", re.I)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False, future=True)
metadata = MetaData()
news = Table(
    "news", metadata,
    Column("id", Integer, primary_key=True),
    Column("src", String(256), nullable=False),
    Column("msg_id", String(64), nullable=False),
    Column("text", Text, nullable=False),
    Column("url", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)
with engine.begin() as conn:
    metadata.create_all(conn)

def parse_keywords():
    return [k.strip() for k in re.split(r"[\s,]+", settings.KEYWORDS) if k.strip()]

def url_to_handle(url: str):
    url = url.strip()
    if not url.startswith("http"): return None
    u = urllib.parse.urlparse(url)
    if not u.netloc.endswith("t.me"): return None
    handle = u.path.strip("/").split("/",1)[0]
    return handle or None

async def fetch_url_text(url: str, timeout=8):
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent":"Mozilla/5.0 (newsbot)"}); r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script","style","noscript"]): t.decompose()
            return " ".join(s.strip() for s in soup.get_text(" ").split())[:5000]
    except Exception:
        return None

async def collect_once():
    kws = parse_keywords()
    raw = [s for s in re.split(r"[\s,]+", settings.SRC_CHANNELS) if s.strip()]
    handles = []
    for s in raw:
        h = url_to_handle(s)
        if h: handles.append(h)
        else: log.warning("skip (not a t.me URL): %s", s)

    async with TelegramClient(StringSession(settings.TELETHON_SESSION),
                              settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH) as client:
        for handle in handles:
            try:
                entity = await client.get_entity(handle)
                src = f"https://t.me/{handle}"
                log.info("reading %s", src)

                async for m in client.iter_messages(entity, limit=200):
                    text = (getattr(m, "raw_text", "") or "").strip()
                    if not text: continue
                    if kws and not any(k.lower() in text.lower() for k in kws): continue

                    url = None
                    found = URL_RX.findall(text)
                    if found:
                        url = found[0]
                        if text.strip() == url:
                            page = await fetch_url_text(url)
                            if page: text = page

                    with engine.begin() as conn:
                        try:
                            conn.execute(insert(news).values(src=src, msg_id=str(m.id), text=text, url=url))
                        except Exception:
                            pass

            except FloodWaitError as fw:
                log.warning("floodwait %s sec on %s", fw.seconds, handle)
                await asyncio.sleep(fw.seconds + 1)
            except Exception as e:
                log.exception("collect failed %s: %s", handle, e)

if __name__ == "__main__":
    asyncio.run(collect_once())
