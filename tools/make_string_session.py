
import getpass
from telethon import TelegramClient
from telethon.sessions import StringSession

print("This tool will create a TELEGRAM_STRING_SESSION for a user account.")
api_id = int(input("API_ID: ").strip())
api_hash = input("API_HASH: ").strip()
phone = input("Phone number (with country code): ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone)
        code = input("Enter the code you received: ").strip()
        client.sign_in(phone=phone, code=code)
        # If you have 2FA enabled, Telethon will ask for password
        try:
            if not client.is_user_authorized():
                pw = getpass.getpass("Two-step verification password: ")
                client.sign_in(password=pw)
        except Exception:
            pass
    print("\nYour TELEGRAM_STRING_SESSION:\n")
    print(client.session.save())
    print("\nStore this in your Railway Variable: TELEGRAM_STRING_SESSION")
