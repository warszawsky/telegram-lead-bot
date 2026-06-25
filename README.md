# 🤖 Telegram Lead & Order Bot

A production-ready Telegram bot for collecting client **leads, orders, questions and support requests** — with an admin workflow and two-way chat between the manager and the client, all through the bot.

Built with **Python 3.12** and **aiogram 3.x** (async). Lightweight, no external services required — data is stored in SQLite.

> 💼 Portfolio project. Demonstrates FSM dialogs, inline keyboards, an admin panel pattern, and a relay (two-way) chat — common building blocks for client-facing Telegram automation.

---

## ✨ Features

- **"Leave a request" flow** with a guided step-by-step dialog (FSM)
- **Category selection:** Service / Order / Question / Support
- Collects **name, contact and task description** (contact via text or the "Share contact" button)
- **Sends every request to an admin chat** as a clean, formatted card
- **Auto-reply** to the client with a confirmation and request number
- **Status workflow** managed by the admin with inline buttons:
  `🆕 New → 🔧 In progress → ✅ Done` — the client is notified on every change
- **Two-way chat:** the manager can message any client *from the bot*, and the client's replies are forwarded back to the admin with a one-tap **Reply** button
- **"My requests"** section for clients to track their own request statuses
- Persistent storage in **SQLite** (survives restarts)
- Configurable via environment variables; Docker-ready for deployment

---

## 🖼 Screenshots

> Add your screenshots to a `screenshots/` folder and reference them here.

| Client side | Admin side |
|---|---|
| ![Request flow](screenshots/client-flow.png) | ![Admin card](screenshots/admin-card.png) |

---

## 🛠 Tech stack

- **Python 3.12**
- **aiogram 3.13** — modern async Telegram Bot framework
- **SQLite** — zero-config persistent storage
- **python-dotenv** — configuration
- **Docker** — containerized deployment

---

## 🚀 Run locally

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in BOT_TOKEN and ADMIN_CHAT_ID
python bot.py
```

Get a token from [@BotFather](https://t.me/BotFather) and your chat id from [@userinfobot](https://t.me/userinfobot).

### Run with Docker

```bash
docker build -t lead-bot .
docker run -e BOT_TOKEN=xxx -e ADMIN_CHAT_ID=123 -v $(pwd)/data:/data lead-bot
```

---

## ⚙️ Configuration

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Bot token from @BotFather |
| `ADMIN_CHAT_ID` | Chat id (personal or group) that receives requests |
| `DB_PATH` | *(optional)* path to the SQLite file (default: `requests.db`) |

---

## 📁 Project structure

```
bot.py             # Bot logic: handlers, FSM dialogs, keyboards
db.py              # SQLite data layer
requirements.txt   # Dependencies
Dockerfile         # Container build
.env.example       # Configuration template
```

---

## 📄 License

MIT — free to use and adapt.
