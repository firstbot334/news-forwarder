import logging, asyncio
from typing import Optional, List
from sqlalchemy import create_engine, MetaData, Table, select, insert
from src.config import settings
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("poster")

def _chunk_text(text: str, maxlen: int = 4000) -> List[str]:
    if not text: return []
    chunks = []
    while len(text) > maxlen:
        # try split at a newline or space near the boundary
        cut = text.rfind("\n", 0, maxlen)
        if cut == -1: cut = text.rfind(" ", 0, maxlen)
        if cut == -1: cut = maxlen
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks

async def send_message(token: str, chat_id: str, text: str) -> Optional[int]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(url, json={"chat_id": chat_id, "text": text})
        try:
            data = r.json()
        except Exception:
            log.error("sendMessage failed: %s", r.text)
            return None
        if not data.get("ok"):
            log.error("sendMessage error: %s", data)
            return None
        return data.get("result", {}).get("message_id")

async def post_once():
    if not settings.BOT_TOKEN or not settings.TARGET_CHANNEL:
        log.warning("BOT_TOKEN or TARGET_CHANNEL not configured; skipping poster")
        return

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False, future=True)
    md = MetaData()
    news = Table("news", md, autoload_with=engine)
    posted = Table("posted", md, autoload_with=engine)

    # Pick newest 50 items that are not yet posted
    with engine.begin() as conn:
        subq = select(posted.c.news_id).subquery()
        rows = conn.execute(
            select(news).where(news.c.id.not_in(select(subq.c.news_id))).order_by(news.c.id.asc()).limit(50)
        ).mappings().all()

    if not rows:
        log.info("no new rows to post")
        return

    for row in rows:
        # Build output text: prefer stored text; append URL if it exists and is not already in text
        text = (row.get("text") or "").strip()
        url = (row.get("url") or "").strip()
        if url and url not in text:
            text = f"{text}\n{url}" if text else url

        if not text:
            # skip empty entries but mark as posted to avoid loop
            with engine.begin() as conn:
                conn.execute(insert(posted).values(news_id=row["id"], posted_msg_id=None))
            continue

        # Split if needed
        parts = _chunk_text(text)
        msg_id: Optional[int] = None
        for idx, part in enumerate(parts):
            sent = await send_message(settings.BOT_TOKEN, settings.TARGET_CHANNEL, part)
            if idx == 0: msg_id = sent
            # Small delay to respect rate limits
            await asyncio.sleep(0.7)

        with engine.begin() as conn:
            conn.execute(insert(posted).values(news_id=row["id"], posted_msg_id=str(msg_id) if msg_id else None))

    log.info("posted %s new rows", len(rows))

if __name__ == "__main__":
    asyncio.run(post_once())
