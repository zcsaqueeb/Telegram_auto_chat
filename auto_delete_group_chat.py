import asyncio
import os
import qrcode
import aiohttp
from datetime import datetime
from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN

# Configuration
SESSION_FOLDER = 'sessions'
SESSION_NAMES = ['user0', 'user1']  # Add more session base names here
GROUP_USERNAME = 'add_here'  # without @
QR_IMAGE_PATH = 'qr_login.png'
CYCLE_DELAY = 300  # Delay between cycles in seconds (now 300 seconds)

# Ensure session folder exists
os.makedirs(SESSION_FOLDER, exist_ok=True)

async def send_qr_to_bot(bot_token, image_path, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    async with aiohttp.ClientSession() as session:
        with open(image_path, 'rb') as photo:
            form = aiohttp.FormData()
            form.add_field('photo', photo, filename="qr.png")
            if caption:
                form.add_field('caption', caption)
            form.add_field('chat_id', str(777000))  # Telegram's login bot
            await session.post(url, data=form)

async def login_with_qr(client, session_name):
    await client.connect()
    if await client.is_user_authorized():
        print(f"✅ [{session_name}] Already logged in.")
        return True

    for attempt in range(3):
        try:
            qr_login = await client.qr_login()
            img = qrcode.make(qr_login.url)
            img.save(QR_IMAGE_PATH)
            await send_qr_to_bot(BOT_TOKEN, QR_IMAGE_PATH, f"[{session_name}] Scan to log in (attempt {attempt+1})")
            print(f"📲 [{session_name}] Waiting for QR scan...")

            await asyncio.wait_for(qr_login.wait(), timeout=120)
            print(f"✅ [{session_name}] Login successful!")
            return True
        except asyncio.TimeoutError:
            print(f"⏱️ [{session_name}] QR scan timed out. Retrying...")
        except Exception as e:
            print(f"⚠️ [{session_name}] QR login failed: {e}")
        finally:
            if os.path.exists(QR_IMAGE_PATH):
                os.remove(QR_IMAGE_PATH)
            await asyncio.sleep(5)
    return False

async def find_group_by_username(client, username):
    try:
        entity = await client.get_entity(username)
        return entity.id
    except Exception as e:
        raise Exception(f"❌ Could not find group by username '{username}': {e}")

async def delete_all_my_messages(client, group_username, session_name):
    group_id = await find_group_by_username(client, group_username)
    my_message_ids = []

    print(f"🔍 [{session_name}] Scanning messages in @{group_username}...")

    async for msg in client.iter_messages(group_id, from_user='me', reverse=True):
        my_message_ids.append(msg.id)

    print(f"🧹 [{session_name}] Found {len(my_message_ids)} messages to delete.")

    if not my_message_ids:
        print(f"ℹ️ [{session_name}] No messages found to delete.")
        return

    for i in range(0, len(my_message_ids), 100):
        chunk = my_message_ids[i:i+100]
        try:
            await client.delete_messages(group_id, chunk, revoke=False)
            print(f"✅ [{session_name}] Deleted {len(chunk)} messages.")
        except Exception as e:
            print(f"⚠️ [{session_name}] Error deleting messages: {e}")
            await asyncio.sleep(5)

    print(f"✅ [{session_name}] Done deleting messages.")

async def process_session(session_base_name):
    session_name = os.path.join(SESSION_FOLDER, session_base_name)
    client = TelegramClient(session_name, API_ID, API_HASH)
    try:
        logged_in = await login_with_qr(client, session_base_name)
        if logged_in:
            await delete_all_my_messages(client, GROUP_USERNAME, session_base_name)
    finally:
        await client.disconnect()

async def main():
    while True:
        print(f"\n🕒 Starting new cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for session_base_name in SESSION_NAMES:
            await process_session(session_base_name)
        print(f"🔁 Cycle complete. Waiting {CYCLE_DELAY} seconds before next run...\n")
        await asyncio.sleep(CYCLE_DELAY)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Interrupted by user.")
