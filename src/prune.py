import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, MetaData, Table, delete
from src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("prune")

def prune():
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False, future=True)
    metadata = MetaData()
    news = Table("news", metadata, autoload_with=engine)
    with engine.begin() as conn:
        cutoff = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=settings.MAX_DAYS_KEEP)
        res = conn.execute(delete(news).where(news.c.created_at < cutoff))
        log.info("pruned %s rows older than %s", res.rowcount, cutoff.isoformat())

if __name__ == "__main__":
    prune()
