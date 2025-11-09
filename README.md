
# Telegram News Forwarder (StringSession Ready)

Headless collector/forwarder that reads **public Telegram channels** and forwards
compact posts to **your target chat/channel**, without any interactive login.
Uses **Telethon StringSession** so Railway/containers can run unattended.

## 1) Environment Variables (Railway → Variables)
- `API_ID` : your Telegram API ID (from https://my.telegram.org)
- `API_HASH` : your Telegram API hash
- `TELEGRAM_STRING_SESSION` : your account **StringSession** (see below)
- `TARGET_CHAT` : where to post the results, e.g. `@mychannel` (or chat ID)
- `CHANNELS` : list of source URLs, one per line or comma+space separated, e.g.
  ```
  https://t.me/nje2e
  https://t.me/bbbbbworld
  https://t.me/repeatandrepeat
  ```
  or `https://t.me/nje2e, https://t.me/bbbbbworld`

- (Optional) `MAX_PER_SOURCE` : default 30
- (Optional) `LOOKBACK_HOURS` : default 12
- (Optional) `POST_MODE` : `simple` (default) | `compact`
- (Optional) `DRY_RUN` : `1` to print to logs only (no posting)

## 2) Make your StringSession (one-time, local)

**Run locally (not inside Railway)**:
```
python tools/make_string_session.py
```
Follow the prompts (phone number, code, and if set, 2FA password).
It will print a long string like `1AQA...`. Put that into `TELEGRAM_STRING_SESSION`.

> You can also run it in any local Python environment. Do **not** share this string.

## 3) Run locally
```
pip install -r requirements.txt
python main.py
```

## 4) Deploy to Railway
- Push this repo to your GitHub, then **New Project → Deploy from Repo**
- Set Variables (above). On deploy, it will start without interaction.
- **Service start command** is defined in `Procfile`.

## 5) What it does
- Logs in with `TELEGRAM_STRING_SESSION`
- Reads each source in `CHANNELS` (t.me URLs only)
- Fetches recent messages (within `LOOKBACK_HOURS`), up to `MAX_PER_SOURCE`
- If a message contains 1+ URLs: forwards a short line per URL to `TARGET_CHAT`
- Deduplicates by message-id+URL to avoid re-post spam
- If a post has text but no URLs, it posts the first 120 chars + link to the original message

## 6) Notes
- Public channels still require an **authenticated API client**; web view ≠ API access.
- If using a **bot** instead of `StringSession`, historical reads are limited; this repo assumes **user session**.
- If a source is private or restricted, your account must have access.
