🤖 Telegram Auto Chat

Welcome to the intersection of memes, market psychology, and message automation. This project combines a modular crypto-themed dialogue generator with a fully automated Telegram bot, creating a one-stop powerhouse for conversation, data training, and vibe deployment.

> "Your seed phrase is your soul. So is your repo structure."

---

## ✨ Features

- 🔥 Generates 2,000+ crypto convo lines, themed around:
  - **Memecoins** (DOGE, PEPE, SHIBA)
  - **L1 Giants** (ETH, SOL, AVAX, MATIC)
  - **Wallet Culture** (zkSync, Phantom, MetaMask)
- 🧘 Reflective alpha: wallet wisdom & trader philosophy
- 💬 400 short replies + 400 extended meme-style sentences
- ⚡ Automated Telegram reply integration via `Telegram_auto_chat`
- 🎛️ Modular files: config, generator, cleaner, and sentence tools

---

## 📦 Setup Instructions

### 1️⃣ Clone Repos

```bash
git clone https://github.com/zcsaqueeb/Telegram_auto_chat.git
cd Telegram_auto_chat
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

No dependencies by default. Add your bot libraries if needed:

```text
python-telegram-bot==20.6
```

### 3️⃣ Run text Generator

```bash
python text_generator.py
```

Creates:

- `cconversation.txt`: convo lines + meme sentences
- Optionally integrates with Telegram bot reply logic

### Then run the main bot script:

```bash
python bot.py
```

### 4️⃣ (Optional) Clean Output ( delete chat in group )

```bash
python auto_delete_group_chat.py
```



## 🗂️ File Structure

| File                  | Purpose                                         |
|-----------------------|-------------------------------------------------|
| `bot.py`         |       Your entrypoint for automation |
| `config.py`           | api_id, api_hash, bot_token,etc       |
| `text_generator.py`   | Generates short and extended crypto sentences (text) |
| `auto_delete_group_chat.py`           | Cleanup tool for generated text               |
| `conversation.txt` | Output file of generated text              |

---

## 🧘 Sample Reflective Lines

- “Trading tests your patience, then your sanity”
- “Market cycles mirror human emotion”
- “HODLing is a meditation”

---

## 🔧 Customize

Add to `config.py`:
- Api_id 
- api_hash
- Bot_Token
- ACCOUNT_COUNT = 2
- TARGET_GROUP_NAME = "here"
- USE_GPT = True ( better to flase)
- GPT_API_URL = "https://gpt-3-5.apis-bj-devs.workers.dev/"  # Fast unofficial endpoint
- # Reply timing configuration
- RESPONSE_DELAY = 3              # Used in responder_loop (faster)
- CHATTER_REPLY_DELAY = 5         # Used in chatter_loop (faster alternating)


Tune conversation length in `generate.py`:
```python
for _ in range(500):  # Adjust for more/less convo lines
```

---

## 🛡 License

MIT — fork it, flex it, vibe responsibly.

---

