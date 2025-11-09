import asyncio
from typing import List, Optional

from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.errors import ChatAdminRequiredError, FloodWaitError

from .config import (
    API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNELS, TARGET_CHANNEL,
    KEYWORDS, POLL_INTERVAL, DB_PATH, FORWARD_MODE, ADD_HEADER
)
from .db import DB

def matches_keywords(text: Optional[str]) -> bool:
    if not KEYWORDS:  # If no keywords, treat as match-all
        return True
    if not text:
        return False
    low = text.lower()
    return any(k in low for k in KEYWORDS)

async def resolve_entity_safe(client: TelegramClient, ident: str):
    # Accept @username or numeric id strings
    try:
        if ident.startswith("@"):
            return await client.get_entity(ident)
        else:
            return await client.get_entity(int(ident))
    except Exception as e:
        print(f"[WARN] Cannot resolve entity {ident!r}: {e}")
        return None

async def fetch_and_forward_once(client: TelegramClient, db: DB):
    target = await resolve_entity_safe(client, TARGET_CHANNEL)
    if not target:
        print("[ERROR] TARGET_CHANNEL not resolvable. Check that the bot has access or is admin of the channel.")
        return

    for src in SOURCE_CHANNELS:
        src_entity = await resolve_entity_safe(client, src)
        if not src_entity:
            continue

        last_id = db.get_last_id(src)
        # Telethon get_messages: use min_id to fetch strictly greater message IDs
        try:
            msgs = await client.get_messages(src_entity, limit=200, min_id=last_id)
        except ChatAdminRequiredError:
            print(f"[WARN] Bot needs to be admin/member to read from {src}. Skipping.")
            continue

        # Messages are returned newest-first; we want chronological order
        msgs = list(reversed(msgs))

        to_forward = []
        max_id = last_id
        for m in msgs:
            # Prefer message text and caption
            text = (m.message or "")

            if matches_keywords(text):
                to_forward.append(m)
            if m.id and m.id > max_id:
                max_id = m.id

        if not to_forward:
            print(f"[INFO] {src}: no new matching posts.")
        else:
            print(f"[INFO] {src}: forwarding {len(to_forward)} posts to {TARGET_CHANNEL}")

        # Forwarding / Copying
        try:
            if to_forward:
                if FORWARD_MODE == "copy":
                    # Copy content as a new message (text only + link to original)
                    for m in to_forward:
                        header = ""
                        if ADD_HEADER:
                            try:
                                src_title = (getattr(src_entity, 'title', None) 
                                             or getattr(src_entity, 'username', None) 
                                             or str(src))
                            except Exception:
                                src_title = str(src)
                            header = f"📡 Source: {src_title}\n"
                        link = ""
                        if m.peer_id and m.id:
                            try:
                                # Public channel short link if username exists
                                uname = getattr(src_entity, 'username', None)
                                if uname:
                                    link = f"\n🔗 https://t.me/{uname}/{m.id}"
                            except Exception:
                                pass
                        await client.send_message(TARGET_CHANNEL, header + (m.message or "(no text)") + link)
                else:
                    # Forward preserves media/formatting (requires permission)
                    await client.forward_messages(TARGET_CHANNEL, to_forward)
        except FloodWaitError as fw:
            print(f"[WARN] Flood wait: sleeping {fw.seconds}s")
            await asyncio.sleep(fw.seconds)
        except Exception as e:
            print(f"[ERROR] Forwarding failed from {src}: {e}")

        # Update checkpoint even if no matching posts (so we don't re-scan)
        if max_id > last_id:
            db.set_last_id(src, max_id)
            print(f"[INFO] {src}: updated last_id -> {max_id}")

async def main():
    if not (API_ID and API_HASH and BOT_TOKEN and SOURCE_CHANNELS and TARGET_CHANNEL):
        print("[ERROR] Missing required env vars: API_ID, API_HASH, BOT_TOKEN, SOURCE_CHANNELS, TARGET_CHANNEL")
        return

    db = DB(DB_PATH)
    client = TelegramClient("bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

    print("[INFO] Bot started. Poll interval:", POLL_INTERVAL, "seconds")
    async with client:
        while True:
            try:
                await fetch_and_forward_once(client, db)
            except Exception as e:
                print("[ERROR] cycle:", e)
            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
