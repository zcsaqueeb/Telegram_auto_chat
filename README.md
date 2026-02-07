# 🤖 Telegram Auto Chat

Welcome to the intersection of memes, market psychology, and message automation. This project combines a modular crypto-themed dialogue generator with a fully automated Telegram bot, creating a one-stop powerhouse for conversation, data training, and vibe deployment.

> "Your seed phrase is your soul. So is your repo structure."

***

## ✨ Features

- 🔥 Generates 2,000+ crypto convo lines, themed around:
  - **Memecoins** (DOGE, PEPE, SHIBA)
  - **L1 Giants** (ETH, SOL, AVAX, MATIC)
  - **Wallet Culture** (zkSync, Phantom, MetaMask)
- 🧘 Reflective alpha: wallet wisdom & trader philosophy
- 💬 400 short replies + 400 extended meme-style sentences
- ⚡ Fully automated Telegram chat playback using Telethon (user accounts, not just bots) [docs.telethon](https://docs.telethon.dev/en/stable/basic/signing-in.html)
- 🎯 Multi-target support:
  - Groups, supergroups, channels
  - Public `@username` and `https://t.me/<name>` links
  - Private invites `https://t.me/+HASH` / `https://t.me/joinchat/HASH` [tl.telethon](https://tl.telethon.dev/methods/messages/import_chat_invite.html)
  - Specific message links like `https://t.me/EPHYRAAI/1` (bot starts by replying to that message)
- 👥 Multi-account:
  - Multiple Telegram user sessions (slots) via phone login or QR login
  - Conversation alternates between `user0`, `user1`, etc.
- 🔁 Smart reply chaining:
  - Optional reply chains that avoid cross-account “Could not find the input entity” errors [stackoverflow](https://stackoverflow.com/questions/70689598/valueerror-could-not-find-the-input-entity-when-using-telethon)
- 🎛️ Modular files: config, generator, cleaner, and sentence tools

***

## 📦 Setup Instructions

### 1️⃣ Clone Repo

```bash
git clone https://github.com/zcsaqueeb/Telegram_auto_chat.git
cd Telegram_auto_chat
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure `requirements.txt` includes (or install manually):

```text
telethon
qrcode
```

(Keep any extra libs you already use.)

### 3️⃣ Create `config.py`

Create `config.py` in the project root:

```python
# config.py

# From https://my.telegram.org/apps
API_ID = 123456
API_HASH = "0123456789abcdef0123456789abcdef"

# From @BotFather
BOT_TOKEN = "123456789:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

# Delay between each scripted message (seconds)
RESPONSE_DELAY = 3
```

Replace with your real `API_ID`, `API_HASH` and `BOT_TOKEN`. [stackoverflow](https://stackoverflow.com/questions/61868770/tegram-bot-api-token-format)

### 4️⃣ Generate Conversation Text

```bash
python text_generator.py
```

This creates:

- `conversation.txt`: lines like  
  `user0: wen airdrop?`  
  `user1: when roadmap, anon?`  

The bot uses these roles (`user0`, `user1`) to choose which user account sends each line.

### 5️⃣ Run the Bot

```bash
python bot.py
```

On first run:

1. Bot creates `sessions/` folder.
2. You talk to your bot in **DM** (not in a group).
3. Use the commands below to log in accounts and set targets.

***

## 🧾 Bot Commands

All commands are sent to the bot in **private chat**.

### Account Setup

- `/setup_accounts`  
  Set how many user accounts you want (slots). Example: send `2` for `user0` and `user1`.

- `/login <slot>`  
  Phone-code login for a slot, e.g. `/login 0`, `/login 1`.  
  It will ask for:
  - Phone number
  - Code from Telegram
  - 2FA password if enabled [docs.telethon](https://docs.telethon.dev/en/stable/basic/signing-in.html)

- `/login_qr <slot>`  
  QR login for a slot, e.g. `/login_qr 0`.  
  The script saves `qr_slot_<slot>.png` – open and scan with the Telegram app. [stackoverflow](https://stackoverflow.com/questions/72518426/how-do-i-authorize-with-a-telethon-qr-code)

- `/logout`  
  Shows a list of logged-in accounts by index, then lets you pick one to log out and remove its session.

### Target Management (Groups / Channels)

Targets are saved in `targets.json` so you don’t touch `config.py` for chats.

- `/add_target <name> <value>`  

  Examples:
  - `/add_target main @MyGroupUsername`
  - `/add_target alpha https://t.me/MyChannel`
  - `/add_target pvt https://t.me/+XXXXXXXXXXXX`
  - `/add_target thread https://t.me/EPHYRAAI/1` (bot starts by replying to message `1` in `@EPHYRAAI`)

  You’ll later start playback with `/start main`, `/start alpha`, etc.

- `/list_targets`  
  Shows all saved targets and their values.

- `/remove_target <name>`  
  Delete one saved target.

- `/clear_targets`  
  Remove all saved targets.

### Script Control

- `/start <target_name>`  
  Starts conversation playback in the specified target.  
  Requirements:
  - At least 2 user slots logged in for `user0`/`user1` alternation.
  - Target name must be defined via `/add_target`.

  The first message:
  - Replies to the message in the `t.me/.../<id>` link if you used that format.
  - Otherwise sends a fresh root message.

- `/stop`  
  Stops playback.

- `/reload`  
  Reloads `conversation.txt` and resets index to `0`.

- `/status`  
  Shows:
  - Whether playback is running
  - Current line index
  - Logged-in accounts and their usernames
  - Session files
  - Saved target names

***

## 🗂️ File Structure

| File                      | Purpose                                                   |
|---------------------------|-----------------------------------------------------------|
| `bot.py`                  | Main Telethon bot: sessions, commands, playback          |
| `config.py`               | API keys, bot token, timing                              |
| `text_generator.py`       | Generates short and long crypto sentences to `conversation.txt` |
| `auto_delete_group_chat.py` | Optional cleanup tool for deleting messages from a group |
| `conversation.txt`        | Generated script: `user0:` / `user1:` conversation lines |
| `targets.json`            | Persisted mapping of target names → chats/links          |
| `sessions/`               | Telethon session files (bot + user accounts)             |

***

## 💬 Conversation Logic

- `conversation.txt` is read top to bottom.
- Each line has a speaker:
  - `user0: ...` → sent by slot 0
  - `user1: ...` → sent by slot 1
- The bot:
  - Optionally replies to a specific message ID if a `t.me/<chat>/<id>` link was used as target.
  - Chains replies only when **the same account** sends consecutive messages, preventing Telethon’s “Could not find the input entity for PeerUser” errors when switching accounts. [stackoverflow](https://stackoverflow.com/questions/69386740/valueerror-could-not-find-the-input-entity-for-peeruser)

You can change pacing by editing `RESPONSE_DELAY` in `config.py`.

***

## 🔧 Customize

- Edit `text_generator.py` to change content style or volume, for example:

  ```python
  for _ in range(500):  # Adjust for more/less convo lines
  ```

- Tweak delays in `config.py` if you want slower or faster conversations.
- Use different targets for different vibes:
  - `/add_target degen @MyMemeGroup`
  - `/add_target serious https://t.me/MyResearchChannel`
  - `/start degen`

***

## 🧘 Sample Reflective Lines

- “Trading tests your patience, then your sanity.”
- “Market cycles mirror human emotion.”
- “HODLing is a meditation.”

***

## 🛡 License

MIT — fork it, flex it, vibe responsibly.
