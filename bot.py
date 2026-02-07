import sys
import asyncio
import os
import pathlib
import logging
import json

import qrcode

from typing import Tuple, Optional

from telethon import TelegramClient, events, errors
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.utils import parse_username

# config.py: API_ID, API_HASH, BOT_TOKEN, RESPONSE_DELAY
from config import API_ID, API_HASH, BOT_TOKEN, RESPONSE_DELAY

LOG_FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger("telethon").setLevel(logging.WARNING)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_DIR = pathlib.Path(".")
SESS_DIR = BASE_DIR / "sessions"
SESS_DIR.mkdir(exist_ok=True)

TARGETS_FILE = BASE_DIR / "targets.json"

conversation = []
turn_index = 0
stop_flag = True
clients = []
client_sessions = []
owner_id = None
desired_accounts = None


# =========================
# CONVERSATION
# =========================

def load_conversation():
    if not os.path.exists("conversation.txt"):
        raise RuntimeError("conversation.txt missing")

    convo = []
    with open("conversation.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            user, msg = line.split(":", 1)
            convo.append((user.strip().lower(), msg.strip()))

    if not convo:
        raise RuntimeError("conversation.txt empty")

    return convo


# =========================
# TARGET STORAGE
# =========================

def load_targets():
    if not TARGETS_FILE.exists():
        return {}
    try:
        with open(TARGETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def save_targets(targets: dict):
    with open(TARGETS_FILE, "w", encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False, indent=2)


# =========================
# SESSIONS / QR
# =========================

def slot_session_name(index: int) -> str:
    return str(SESS_DIR / f"account{index}.session")


def list_session_files() -> list[str]:
    return [
        str(p) for p in SESS_DIR.glob("*.session")
        if p.name != "bot.session"
    ]


def save_qr_to_file(url: str, index: int) -> str:
    img = qrcode.make(url)
    filename = f"qr_slot_{index}.png"
    img.save(filename)
    logging.info(f"QR for slot {index} saved to {filename}")
    return os.path.abspath(filename)


# =========================
# PHONE LOGIN PER SLOT
# =========================

async def login_slot_once(bot: TelegramClient, event, index: int):
    session_path = slot_session_name(index)
    sender = event.sender_id

    async with bot.conversation(sender, timeout=120) as conv:
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()

        if await client.is_user_authorized():
            me = await client.get_me()
            await conv.send_message(
                f"✅ Slot {index} already logged in as @{me.username or me.id}\n"
                f"Session: `{os.path.basename(session_path)}`",
                parse_mode="markdown"
            )
            await client.disconnect()
            return session_path

        ask_phone = await conv.send_message(
            f"📱 Send phone number for slot {index} (with country code, e.g. +91xxxxxxxxxx):"
        )
        try:
            phone_msg = await conv.get_response()
        except asyncio.TimeoutError:
            await conv.send_message("⌛ Timeout waiting for phone. Use /login again.")
            await ask_phone.delete()
            await client.disconnect()
            return None

        phone = phone_msg.text.strip()

        await conv.send_message(f"⏳ Sending login code to `{phone}` ...")
        try:
            sent = await client.send_code_request(phone)
        except errors.FloodWaitError as e:
            await conv.send_message(
                f"⛔ Flood wait on sending code. Wait {e.seconds} seconds then try again."
            )
            await client.disconnect()
            return None
        except errors.PhoneNumberInvalidError:
            await conv.send_message("❌ Invalid phone number.")
            await client.disconnect()
            return None
        except Exception as e:
            logging.error(f"send_code_request failed: {e}")
            await conv.send_message(f"❌ Error sending code: `{e}`")
            await client.disconnect()
            return None

        ask_code = await conv.send_message("🔑 Send the login code you received:")
        try:
            code_msg = await conv.get_response(timeout=180)
        except asyncio.TimeoutError:
            await conv.send_message("⌛ Timeout waiting for code. Use /login again.")
            await client.disconnect()
            return None

        code = code_msg.text.strip()

        try:
            await client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=sent.phone_code_hash
            )
        except errors.PhoneCodeExpiredError:
            await conv.send_message("❌ Code expired. Use /login again.")
            await client.disconnect()
            return None
        except errors.PhoneCodeInvalidError:
            await conv.send_message("❌ Invalid code. Use /login again.")
            await client.disconnect()
            return None
        except errors.SessionPasswordNeededError:
            ask_pass = await conv.send_message("🔒 2FA enabled. Send your 2FA password:")
            try:
                pass_msg = await conv.get_response(timeout=180)
            except asyncio.TimeoutError:
                await conv.send_message("⌛ Timeout waiting for 2FA password.")
                await client.disconnect()
                return None

            password = pass_msg.text.strip()
            try:
                await client.sign_in(password=password)
            except Exception as e:
                logging.error(f"2FA error: {e}")
                await conv.send_message(f"❌ 2FA login failed: `{e}`.")
                await client.disconnect()
                return None
        except Exception as e:
            logging.error(f"sign_in failed: {e}")
            await conv.send_message(f"❌ Login failed: `{e}`.")
            await client.disconnect()
            return None

        me = await client.get_me()
        await client.disconnect()
        await conv.send_message(
            f"✅ Slot {index} logged in as @{me.username or me.id}\n"
            f"💾 Session saved as `{os.path.basename(session_path)}`",
            parse_mode="markdown"
        )
        return session_path


# =========================
# QR LOGIN PER SLOT
# =========================

async def login_slot_qr(bot: TelegramClient, event, index: int):
    session_path = slot_session_name(index)
    sender = event.sender_id

    async with bot.conversation(sender, timeout=300) as conv:
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()

        if await client.is_user_authorized():
            me = await client.get_me()
            await conv.send_message(
                f"✅ Slot {index} already logged in as @{me.username or me.id}\n"
                f"Session: `{os.path.basename(session_path)}`",
                parse_mode="markdown"
            )
            await client.disconnect()
            return session_path

        await conv.send_message(
            f"📷 QR login for slot {index}.\n"
            "I will save a QR image in this folder, open it and scan with Telegram."
        )

        qr_path = None

        try:
            qr_login = await client.qr_login()

            qr_path = save_qr_to_file(qr_login.url, index)
            await conv.send_message(
                f"✅ QR for slot {index} saved as:\n`{qr_path}`\n"
                "Open that image and scan it with Telegram app, then wait.",
                parse_mode="markdown"
            )

            try:
                await qr_login.wait(timeout=180)
            except errors.SessionPasswordNeededError:
                await conv.send_message("🔒 2FA enabled. Send your 2FA password for this account:")
                try:
                    pass_msg = await conv.get_response(timeout=180)
                except asyncio.TimeoutError:
                    await conv.send_message("⌛ Timeout waiting for 2FA password.")
                    await client.disconnect()
                    return None
                password = pass_msg.text.strip()
                await client.sign_in(password=password)
            except asyncio.TimeoutError:
                await conv.send_message("⌛ QR login timed out. Use /login_qr again.")
                await client.disconnect()
                return None

        except errors.FloodWaitError as e:
            await conv.send_message(
                f"⛔ Flood wait on QR login. Wait {e.seconds} seconds then try again."
            )
            await client.disconnect()
            return None

        me = await client.get_me()
        await client.disconnect()

        if qr_path and os.path.exists(qr_path):
            try:
                os.remove(qr_path)
            except Exception:
                pass

        await conv.send_message(
            f"✅ Slot {index} logged in via QR as @{me.username or me.id}\n"
            f"💾 Session saved as `{os.path.basename(session_path)}`",
            parse_mode="markdown"
        )
        return session_path


# =========================
# TARGET RESOLVER (WITH MESSAGE LINK SUPPORT)
# =========================

async def resolve_target_chat_and_msg(client: TelegramClient, target: str) -> Tuple[object, Optional[int]]:
    """
    Return (entity, base_reply_msg_id) for a target.
    Supports:
    - @username
    - t.me links (plain or /<msg_id>)
    - invite links (t.me/+HASH, t.me/joinchat/HASH)
    - name fragments
    Example targets:
        '@EPHYRAAI'
        'https://t.me/EPHYRAAI/1'
        'EPHYRAAI/channel/1'
    """
    t = target.strip()
    base_reply_id: Optional[int] = None

    # t.me/EPHYRAAI/1
    if "t.me/" in t:
        after = t.split("t.me/")[1]
        parts = after.split("/")
        if len(parts) >= 2 and parts[-1].isdigit():
            base_reply_id = int(parts[-1])
            t = "https://t.me/" + "/".join(parts[:-1])

    # custom form: EPHYRAAI/channel/1  or @EPHYRAAI/channel/1
    if "/channel/" in t:
        head, tail = t.split("/channel/", 1)
        if tail.isdigit():
            base_reply_id = int(tail)
            t = head

    # 1) Direct get_entity
    try:
        entity = await client.get_entity(t)
        return entity, base_reply_id
    except Exception:
        pass

    # 2) Parse username from different forms (@user, t.me/user, user)
    try:
        username, _, _ = parse_username(t)
        if username:
            entity = await client.get_entity(username)
            return entity, base_reply_id
    except Exception:
        pass

    # 3) Private invite links
    if "t.me/" in t:
        try:
            part = t.split("t.me/")[1]
            part = part.split("?")[0].strip("/")

            invite_hash = None
            if part.startswith("+"):
                invite_hash = part[1:]
            elif part.startswith("joinchat/"):
                invite_hash = part.split("joinchat/")[1]

            if invite_hash:
                res = await client(ImportChatInviteRequest(invite_hash))
                if getattr(res, "chats", None):
                    return res.chats[0], base_reply_id
        except Exception:
            pass

    # 4) Fallback: search dialogs by title fragment
    name_lc = t.lower()
    candidates = []
    async for d in client.iter_dialogs():
        if name_lc in (d.name or "").lower():
            candidates.append(d)

    if not candidates:
        raise RuntimeError(
            f"Target chat not found for '{target}'. "
            f"Join the group/channel first or check the username/link."
        )

    return candidates[0].entity, base_reply_id


# =========================
# SCRIPT PLAYER (REPLY CHAIN, SAFE)
# =========================

async def chatter_loop(group_id, base_reply_msg_id=None):
    """
    First bot message:
      - if base_reply_msg_id is given → reply to that message (from t.me/.../id link)
      - else: fresh message.
    Later:
      - reply only when the same Telethon client sends again,
        to avoid cross-account PeerUser entity errors.
    """
    global turn_index, stop_flag
    logging.info("🗣️ Script playback started")

    last_msg_id = None
    last_sender_index = None

    while not stop_flag and turn_index < len(conversation):
        user, msg = conversation[turn_index]

        if user == "user0":
            sender_index = 0
        elif user == "user1":
            sender_index = 1 if len(clients) > 1 else 0
        else:
            sender_index = 0

        sender = clients[sender_index]

        try:
            reply_to_id = None
            if base_reply_msg_id is not None and last_msg_id is None:
                reply_to_id = base_reply_msg_id
            elif last_msg_id is not None and sender_index == last_sender_index:
                reply_to_id = last_msg_id

            if reply_to_id is None:
                sent = await sender.send_message(group_id, msg)
            else:
                sent = await sender.send_message(group_id, msg, reply_to=reply_to_id)

            last_msg_id = sent.id
            last_sender_index = sender_index

            logging.info(
                f"[{user}] {msg} (reply_to={reply_to_id}, sender_index={sender_index})"
            )
            turn_index += 1

        except Exception as e:
            logging.error(e)
            await asyncio.sleep(5)
            continue

        await asyncio.sleep(RESPONSE_DELAY)

    logging.info("✅ Conversation finished or stopped")


# =========================
# COMMAND HANDLER
# =========================

async def command_handler(bot: TelegramClient):
    global stop_flag, conversation, turn_index, clients, client_sessions, owner_id, desired_accounts

    me_bot = await bot.get_me()
    logging.info(f"Bot started as @{me_bot.username or me_bot.id}")

    @bot.on(events.NewMessage(pattern=r'^/(start|status|stop|reload|login|login_qr|logout|setup_accounts|add_target|list_targets|remove_target|clear_targets)(?:\s+.*)?$'))
    async def handler(event):
        global stop_flag, conversation, turn_index, clients, client_sessions, owner_id, desired_accounts

        if event.is_group or event.is_channel:
            return

        if owner_id is None:
            owner_id = event.sender_id
        if event.sender_id != owner_id:
            return

        text = event.raw_text.strip()
        parts = text.split()
        cmd = parts[0].lower()

        targets = load_targets()

        # ===== TARGET MANAGEMENT =====

        if cmd == "/add_target":
            if len(parts) < 3:
                await event.reply(
                    "Usage:\n`/add_target <name> <@username|t.me/link|title_fragment|t.me/channel/1>`",
                    parse_mode="markdown"
                )
                return
            name = parts[1]
            value = " ".join(parts[2:])
            targets[name] = value
            save_targets(targets)
            await event.reply(
                f"✅ Target `{name}` saved as:\n`{value}`",
                parse_mode="markdown"
            )
            return

        if cmd == "/list_targets":
            if not targets:
                await event.reply("No targets saved.")
                return
            lines = [f"`{k}` → `{v}`" for k, v in targets.items()]
            await event.reply(
                "🎯 Saved targets:\n" + "\n".join(lines),
                parse_mode="markdown"
            )
            return

        if cmd == "/remove_target":
            if len(parts) < 2:
                await event.reply("Usage:\n`/remove_target <name>`", parse_mode="markdown")
                return
            name = parts[1]
            if name not in targets:
                await event.reply(f"❌ Target `{name}` not found.", parse_mode="markdown")
                return
            del targets[name]
            save_targets(targets)
            await event.reply(f"🗑️ Target `{name}` removed.", parse_mode="markdown")
            return

        if cmd == "/clear_targets":
            save_targets({})
            await event.reply("🧹 All targets cleared.")
            return

        # ===== SETUP ACCOUNTS / LOGIN =====

        if cmd == "/setup_accounts":
            async with bot.conversation(event.sender_id, timeout=60) as conv:
                msg_q = await conv.send_message(
                    "🧩 How many user accounts do you want to login? (1–10)\n"
                    "Example: send `2` for slot 0 and slot 1."
                )
                try:
                    resp = await conv.get_response(timeout=60)
                except asyncio.TimeoutError:
                    await conv.send_message("⌛ Timeout. Run /setup_accounts again.")
                    await msg_q.delete()
                    return

                txt = resp.text.strip()
                try:
                    n = int(txt)
                except ValueError:
                    await conv.send_message("❌ Please send a number between 1 and 10.")
                    await msg_q.delete()
                    return

                if not 1 <= n <= 10:
                    await conv.send_message("❌ Number must be between 1 and 10.")
                    await msg_q.delete()
                    return

                desired_accounts = n
                await conv.send_message(
                    f"✅ Will use {n} accounts.\n"
                    "Use `/login <slot>` or `/login_qr <slot>` to login each slot.",
                    parse_mode="markdown"
                )
                await msg_q.delete()
                try:
                    await resp.delete()
                except Exception:
                    pass
            return

        if cmd == "/login":
            if len(parts) == 1:
                await event.reply(
                    "📲 Login usage (phone):\n"
                    "`/login 0` or `/login 1` etc.",
                    parse_mode="markdown"
                )
                return

            try:
                index = int(parts[1])
            except ValueError:
                await event.reply("❌ Slot must be a number, e.g. `/login 0`.", parse_mode="markdown")
                return

            if index < 0 or index > 20:
                await event.reply("❌ Slot must be between 0 and 20.")
                return

            session_file = await login_slot_once(bot, event, index)
            if session_file:
                if session_file not in client_sessions:
                    new_client = TelegramClient(session_file, API_ID, API_HASH)
                    await new_client.start()
                    clients.append(new_client)
                    client_sessions.append(session_file)

                extra = ""
                if desired_accounts is not None:
                    remaining = desired_accounts - len(clients)
                    if remaining > 0:
                        extra = (
                            f"\nYou still need to login {remaining} more account(s). "
                            "Run `/login <slot>` or `/login_qr <slot>` again."
                        )
                    else:
                        extra = "\nAll desired accounts are logged in. You can /start <target> now."
                await event.reply(
                    f"✅ Slot {index} ready. Total accounts: {len(clients)}{extra}",
                    parse_mode="markdown"
                )
            return

        if cmd == "/login_qr":
            if len(parts) == 1:
                await event.reply(
                    "📷 QR login usage:\n"
                    "`/login_qr 0` or `/login_qr 1` etc.",
                    parse_mode="markdown"
                )
                return

            try:
                index = int(parts[1])
            except ValueError:
                await event.reply("❌ Slot must be a number, e.g. `/login_qr 0`.", parse_mode="markdown")
                return

            if index < 0 or index > 20:
                await event.reply("❌ Slot must be between 0 and 20.")
                return

            session_file = await login_slot_qr(bot, event, index)
            if session_file:
                if session_file not in client_sessions:
                    new_client = TelegramClient(session_file, API_ID, API_HASH)
                    await new_client.start()
                    clients.append(new_client)
                    client_sessions.append(session_file)

                extra = ""
                if desired_accounts is not None:
                    remaining = desired_accounts - len(clients)
                    if remaining > 0:
                        extra = (
                            f"\nYou still need to login {remaining} more account(s). "
                            "Run `/login <slot>` or `/login_qr <slot>` again."
                        )
                    else:
                        extra = "\nAll desired accounts are logged in. You can /start <target> now."
                await event.reply(
                    f"✅ Slot {index} ready via QR. Total accounts: {len(clients)}{extra}",
                    parse_mode="markdown"
                )
            return

        if cmd == "/logout":
            if not clients:
                await event.reply("No accounts to logout.")
                return

            lines = []
            for i, c in enumerate(clients):
                try:
                    me = await c.get_me()
                    lines.append(f"{i}: @{me.username or me.id}")
                except Exception:
                    lines.append(f"{i}: (error)")
            await event.reply("Send index of account to logout:\n" + "\n".join(lines))

            async with bot.conversation(event.sender_id) as conv:
                resp = await conv.get_response()
                try:
                    idx = int(resp.text.strip())
                except ValueError:
                    await conv.send_message("❌ Invalid index.")
                    return

                if idx < 0 or idx >= len(clients):
                    await conv.send_message("❌ Index out of range.")
                    return

                client = clients[idx]
                sess = client_sessions[idx]

                try:
                    await client.log_out()
                except Exception as e:
                    logging.error(f"logout error: {e}")
                await client.disconnect()

                del clients[idx]
                del client_sessions[idx]

                try:
                    os.remove(sess)
                except FileNotFoundError:
                    pass

                await conv.send_message(
                    f"✅ Logged out and removed session `{os.path.basename(sess)}`."
                )
            return

        # ===== SCRIPT CONTROL =====

        if cmd == "/start":
            if len(parts) < 2:
                await event.reply(
                    "Usage:\n`/start <target_name>`\n\n"
                    "Use `/list_targets` to see available names.",
                    parse_mode="markdown"
                )
                return

            target_name = parts[1]
            if target_name not in targets:
                await event.reply(
                    f"❌ Target `{target_name}` not found. Add it with:\n"
                    "`/add_target mychat @username_or_link`",
                    parse_mode="markdown"
                )
                return

            if desired_accounts is not None and len(clients) < desired_accounts:
                await event.reply(
                    f"⚠️ You set {desired_accounts} accounts but only {len(clients)} logged in.\n"
                    "Login more with `/login <slot>` or `/login_qr <slot>`.",
                    parse_mode="markdown"
                )
                return
            if len(clients) == 0:
                await event.reply("⚠️ No user accounts logged in. Use /setup_accounts and /login.")
                return
            if len(clients) == 1:
                await event.reply("⚠️ Only 1 account logged in. For user0/user1 conversation, login second slot.")
                return
            if not stop_flag:
                await event.reply("▶️ Already running.")
                return

            stop_flag = False
            target_value = targets[target_name]

            try:
                entity, base_reply_id = await resolve_target_chat_and_msg(clients[0], target_value)
                group_id = entity.id
            except RuntimeError as e:
                stop_flag = True
                await event.reply(
                    f"❌ Cannot resolve target `{target_name}` = `{target_value}`:\n{e}",
                    parse_mode="markdown"
                )
                return

            await event.reply(
                f"▶️ Chat playback started in `{target_name}` (`{target_value}`).",
                parse_mode="markdown"
            )
            asyncio.create_task(chatter_loop(group_id, base_reply_msg_id=base_reply_id))
            return

        if cmd == "/stop":
            stop_flag = True
            await event.reply("⛔ Chat playback stopped.")
            return

        if cmd == "/reload":
            conversation = load_conversation()
            turn_index = 0
            await event.reply("🔄 conversation.txt reloaded, index reset to 0.")
            return

        if cmd == "/status":
            acc_lines = []
            for i, c in enumerate(clients):
                try:
                    me = await c.get_me()
                    uname = me.username or "no_username"
                    acc_lines.append(f"{i}. @{uname} (id: {me.id})")
                except Exception:
                    acc_lines.append(f"{i}. (error reading account)")

            sessions = [os.path.basename(s) for s in client_sessions]
            targets = load_targets()

            txt = (
                "📊 <b>Bot Status</b>\n"
                f"• Chat running: {'✅ yes' if not stop_flag else '⏸ no'}\n"
                f"• Turn index: <code>{turn_index}/{len(conversation)}</code>\n"
                f"• Desired accounts: {desired_accounts if desired_accounts is not None else 'not set'}\n\n"
                "👥 <b>Accounts</b>\n"
                f"{chr(10).join(acc_lines) if acc_lines else 'none'}\n\n"
                "💾 <b>Session files</b>\n"
                f"{', '.join(sessions) if sessions else 'none'}\n\n"
                "🎯 <b>Targets</b>\n"
                f"{', '.join(targets.keys()) if targets else 'none'}"
            )
            await event.reply(txt, parse_mode="html")
            return


# =========================
# MAIN
# =========================

async def main():
    global clients, conversation, client_sessions, owner_id

    bot = TelegramClient(str(SESS_DIR / "bot"), API_ID, API_HASH)
    try:
        await bot.start(bot_token=BOT_TOKEN)
    except errors.FloodWaitError as e:
        wait_time = int(e.seconds) + 5
        logging.warning(f"FloodWait on bot login: wait {e.seconds}s. Sleeping {wait_time}s and exiting.")
        await asyncio.sleep(wait_time)
        return

    # load existing user sessions
    for sess in list_session_files():
        if os.path.basename(sess) == "bot.session":
            continue
        client = TelegramClient(sess, API_ID, API_HASH)
        await client.start()
        clients.append(client)
        client_sessions.append(sess)

    logging.info(f"Loaded {len(clients)} user sessions.")

    conversation = load_conversation()

    await command_handler(bot)

    await bot.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Stopped manually")
