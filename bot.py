import sys
import asyncio
import os
import random
import aiohttp
import qrcode
import difflib
import re
import logging
from telethon import TelegramClient, events
from telethon.errors import ChannelInvalidError
from config import *

# 🪵 Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.makedirs("sessions", exist_ok=True)

prompt_reply_map = {}
clients = []
stop_flag = False
last_sent_message = None
recent_messages = []
MAX_RECENT = 10

def load_prompt_reply_map():
    user_map = {}
    if not os.path.exists("conversation.txt"):
        return user_map
    with open("conversation.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                try:
                    user, message = line.split(":", 1)
                    user = user.strip().lower()
                    message = message.strip()
                    if user and message:
                        user_map.setdefault(user, []).append(message)
                except Exception as e:
                    logging.warning(f"Failed to parse line: {line} | Error: {e}")
                    continue
    return user_map

prompt_reply_map = load_prompt_reply_map()

async def generate_message(prompt=None):
    all_messages = sum(prompt_reply_map.values(), [])
    if not all_messages:
        return "Let's talk Avengers."

    filtered = [m for m in all_messages if m.lower() not in [m.lower() for m in recent_messages]]

    if filtered:
        msg = random.choice(filtered)
    else:
        msg = random.choice(all_messages)

    recent_messages.append(msg)
    if len(recent_messages) > MAX_RECENT:
        recent_messages.pop(0)

    logging.info(f"Generated message: {msg}")
    return msg

async def chatter_loop(clients, group_id):
    global stop_flag, last_sent_message
    chatter = clients[1]
    first_message_sent = False

    logging.info("🗣️ Starting chatter loop...")

    while not stop_flag:
        msg = await generate_message(last_sent_message if first_message_sent else None)
        first_message_sent = True

        try:
            await chatter.send_message(group_id, msg)
            logging.info(f"📤 Sent: {msg}")
            last_sent_message = msg
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            await asyncio.sleep(5)
            continue

        await asyncio.sleep(60)  # ⏱️ Delay 1 min before generating reply

        reply = await generate_message(last_sent_message)
        if not reply:
            await asyncio.sleep(5)
            continue

        try:
            await chatter.send_message(group_id, reply)
            logging.info(f"📤 Reply: {reply}")
            last_sent_message = reply
        except Exception as e:
            logging.error(f"Error sending reply: {e}")
            await asyncio.sleep(5)
            continue

        await asyncio.sleep(60)

async def send_qr_to_bot(bot_token, image_path, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    async with aiohttp.ClientSession() as session:
        with open(image_path, 'rb') as photo:
            form = aiohttp.FormData()
            form.add_field('photo', photo, filename="qr.png")
            if caption:
                form.add_field('caption', caption)
            form.add_field('chat_id', str(777000))
            await session.post(url, data=form)
            logging.info(f"📸 QR sent to bot: {image_path}")

async def login_with_qr(index):
    session_file = os.path.join("sessions", f"user{index}.session")
    client = TelegramClient(session_file, API_ID, API_HASH)
    await client.connect()
    if await client.is_user_authorized():
        await client.disconnect()
        logging.info(f"✅ user{index} already authorized.")
        return

    img_path = f"qr_user{index}.png"

    for attempt in range(3):
        try:
            qr_login = await client.qr_login()
            img = qrcode.make(qr_login.url)
            img.save(img_path)
            await send_qr_to_bot(BOT_TOKEN, img_path, f"Scan to log in user{index} (attempt {attempt+1})")
            await qr_login.wait()
            logging.info(f"🔓 Logged in user{index} via QR.")
            break
        except Exception as e:
            logging.warning(f"Login attempt {attempt+1} for user{index} failed: {e}")
            await asyncio.sleep(5)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)
    await client.disconnect()

async def login_all_accounts():
    logging.info("🔐 Logging in all accounts...")
    tasks = [login_with_qr(i) for i in range(2)]
    await asyncio.gather(*tasks)

async def find_group(client):
    async for dialog in client.iter_dialogs():
        if dialog.is_group and (
            TARGET_GROUP_NAME.lower() in dialog.name.lower() or
            getattr(dialog.entity, "username", "").lower() == TARGET_GROUP_NAME.lower()
        ):
            logging.info(f"📍 Group '{dialog.name}' found with ID {dialog.id}")
            return dialog.id
    raise Exception(f"Group '{TARGET_GROUP_NAME}' not found.")

async def responder_loop(responder, group_id, allowed_ids):
    @responder.on(events.NewMessage(chats=group_id))
    async def handler(event):
        global stop_flag
        if stop_flag:
            return
        sender = await event.get_sender()
        if sender.id not in allowed_ids:
            logging.info("Message ignored from unauthorized user.")
            return

        text = event.raw_text.strip()
        delay = RESPONSE_DELAY + random.randint(-5, 5)
        await asyncio.sleep(delay)

        reply = await generate_message(text)
        if not reply:
            return
        await responder.send_message(group_id, reply, reply_to=event.id)
        logging.info(f"💬 Replied to message with: {reply}")

async def add_status_commands(bot_client):
    bot_user = await bot_client.get_me()

    @bot_client.on(events.NewMessage(pattern=r'^/(start|status|stop|reload)$'))
    async def handler(event):
        global stop_flag, prompt_reply_map
        sender = await event.get_sender()
        if sender.id != bot_user.id:
            return
        cmd = event.raw_text.strip().lower()
        logging.info(f"⚙️ Received command: {cmd}")
        try:
            if cmd == "/start":
                await event.reply("🤖 Bot is initialized and ready.")
            elif cmd == "/status":
                await event.reply("✅ Bot is running and all systems are active.")
            elif cmd == "/stop":
                stop_flag = True
                await event.reply("🛑 Bot has been stopped. No further messages will be sent.")
            elif cmd == "/reload":
                prompt_reply_map = load_prompt_reply_map()
                await event.reply("🔄 Conversation map reloaded.")
        except Exception as e:
            logging.error(f"Command error: {e}")
            await event.reply(f"⚠️ Command error: {e}")

async def main():
    global clients
    session_paths = [os.path.join("sessions", f"user{i}.session") for i in range(2)]
    if not all(os.path.exists(path) for path in session_paths):
        await login_all_accounts()

    clients = [TelegramClient(session_paths[i], API_ID, API_HASH) for i in range(2)]
    await asyncio.gather(*[c.start() for c in clients])
    logging.info("📶 All clients started.")

    group_id = await find_group(clients[0])
    me = await clients[1].get_me()
    asyncio.create_task(chatter_loop(clients, group_id))
    await add_status_commands(clients[0])
    await responder_loop(clients[0], group_id, [me.id])
    await clients[0].run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("KeyboardInterrupt received. Shutting down...")
