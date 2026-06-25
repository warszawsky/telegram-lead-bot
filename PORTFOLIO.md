# Текст для портфолио Upwork (копируй-вставляй)

## Заголовок проекта (Project title)
Telegram Bot for Lead & Order Collection with Admin Workflow

## Краткое описание (для карточки портфолио)
A Telegram bot that turns chats into a sales/support pipeline: clients leave
requests (service, order, question, support), the bot collects their details,
notifies the manager, and supports a full status workflow plus two-way chat —
the manager replies to clients directly from the bot.

## Полное описание (Overview)
I designed and built a production-ready Telegram bot in Python (aiogram 3, async)
that automates intake of client requests for small businesses.

Key features:
• Guided "Leave a request" dialog with category selection (service / order /
  question / support) using a finite-state machine.
• Collects name, contact (text or one-tap "Share contact"), and task description.
• Forwards every request to an admin chat as a clean formatted card.
• Status workflow (New → In progress → Done) controlled by the admin via inline
  buttons; the client is automatically notified on each change.
• Two-way relay chat: the manager messages any client from the bot, and client
  replies are forwarded back with a one-tap "Reply" button.
• Persistent SQLite storage; Docker-ready; configured via environment variables.

The architecture is clean and modular (handlers, FSM states, data layer separated),
making it easy to extend with payments, CRM integration, or Google Sheets export.

## Skills / tags
Python, aiogram, Telegram Bot API, asyncio, SQLite, Docker, FSM, automation, chatbot

---

## Что приложить к карточке портфолио
1. Ссылку на GitHub-репозиторий.
2. 3-5 скриншотов (см. screenshots/HOW_TO.txt) или короткое демо-видео/GIF.
3. (Опционально) ссылку на живого бота в Telegram, если решишь оставить его включённым.

## Совет по Upwork
- Сделай отдельную "Portfolio item" с картинкой-обложкой (можно коллаж из скриншотов).
- В первом предложении — польза для клиента ("turns chats into a sales pipeline"),
  а не технологии. Технологии — ниже, в тегах.
- Если есть возможность — запиши 20-30 сек видео-демо: это сильно повышает доверие.
