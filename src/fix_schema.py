import logging
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, func, UniqueConstraint
from src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("schema")

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
    UniqueConstraint("src", "msg_id", name="uq_news_src_msg"),
)

posted = Table(
    "posted", metadata,
    Column("id", Integer, primary_key=True),
    Column("news_id", Integer, nullable=False, unique=True),
    Column("posted_msg_id", String(64), nullable=True),
    Column("posted_at", DateTime(timezone=True), server_default=func.now()),
)

with engine.begin() as conn:
    metadata.create_all(conn)
    log.info("✅ schema ensured (news, posted)")
