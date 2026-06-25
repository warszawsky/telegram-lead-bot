"""
Телеграм-бот для приёма заявок и заказов.

Функционал:
  • Кнопка «Оставить заявку»
  • Выбор категории: услуга / заказ / вопрос / поддержка
  • Сбор имени, контакта и описания задачи
  • Отправка заявки в админ-чат
  • Автоответ пользователю с подтверждением
  • Статусы заявки: принято / в работе / готово (меняет админ)
"""
import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

import db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

if not BOT_TOKEN:
    raise SystemExit("Не задан BOT_TOKEN. Скопируй .env.example в .env и заполни.")
if not ADMIN_CHAT_ID:
    raise SystemExit("Не задан ADMIN_CHAT_ID. Заполни его в .env.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Категории заявок: код -> подпись
CATEGORIES = {
    "service": "🛠 Услуга",
    "order": "🛒 Заказ",
    "question": "❓ Вопрос",
    "support": "🆘 Поддержка",
}


# ─────────────────────────── FSM ───────────────────────────
class NewRequest(StatesGroup):
    category = State()
    name = State()
    contact = State()
    description = State()


class AdminReply(StatesGroup):
    message = State()


def is_admin(user_id: int, chat_id: int) -> bool:
    """Проверка, что действие совершает админ (личка админа или админ-чат/группа)."""
    return chat_id == ADMIN_CHAT_ID or user_id == ADMIN_CHAT_ID


# ─────────────────────────── Клавиатуры ───────────────────────────
def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Оставить заявку")],
            [KeyboardButton(text="📋 Мои заявки")],
        ],
        resize_keyboard=True,
    )


def categories_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"cat:{code}")]
        for code, label in CATEGORIES.items()
    ]
    rows.append([InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def admin_status_kb(request_id: int, with_status: bool = True) -> InlineKeyboardMarkup:
    rows = []
    if with_status:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔧 В работу", callback_data=f"st:{request_id}:{db.STATUS_IN_PROGRESS}"
                ),
                InlineKeyboardButton(
                    text="✅ Готово", callback_data=f"st:{request_id}:{db.STATUS_DONE}"
                ),
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="✉️ Написать клиенту", callback_data=f"reply:{request_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ─────────────────────────── Команды ───────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👋 Привет! Я бот для приёма заявок и заказов.\n\n"
        "Нажми «📝 Оставить заявку», чтобы начать.",
        reply_markup=main_menu(),
    )


@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Нечего отменять.", reply_markup=main_menu())
        return
    await state.clear()
    await message.answer("Заявка отменена.", reply_markup=main_menu())


@dp.message(F.text == "📋 Мои заявки")
async def my_requests(message: Message) -> None:
    rows = db.list_user_requests(message.from_user.id)
    if not rows:
        await message.answer("У тебя пока нет заявок.", reply_markup=main_menu())
        return
    lines = ["<b>Твои заявки:</b>\n"]
    for r in rows:
        lines.append(
            f"#{r['id']} — {CATEGORIES.get(r['category'], r['category'])} — "
            f"{db.STATUS_LABELS.get(r['status'], r['status'])}"
        )
    await message.answer("\n".join(lines), reply_markup=main_menu())


# ─────────────────────────── Сценарий заявки ───────────────────────────
@dp.message(F.text == "📝 Оставить заявку")
@dp.message(Command("new"))
async def start_request(message: Message, state: FSMContext) -> None:
    await state.set_state(NewRequest.category)
    await message.answer(
        "Выбери категорию заявки:",
        reply_markup=categories_kb(),
    )


@dp.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Заявка отменена.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(NewRequest.category, F.data.startswith("cat:"))
async def choose_category(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    if code not in CATEGORIES:
        await callback.answer("Неизвестная категория", show_alert=True)
        return
    await state.update_data(category=code)
    await state.set_state(NewRequest.name)
    await callback.message.edit_text(f"Категория: {CATEGORIES[code]}")
    await callback.message.answer("Как тебя зовут? (имя)")
    await callback.answer()


@dp.message(NewRequest.name, F.text)
async def get_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое, попробуй ещё раз.")
        return
    await state.update_data(name=name)
    await state.set_state(NewRequest.contact)
    await message.answer(
        "Оставь контакт для связи (телефон, @username или email).\n"
        "Можешь нажать кнопку ниже, чтобы поделиться номером.",
        reply_markup=contact_kb(),
    )


@dp.message(NewRequest.contact, F.contact)
async def get_contact_button(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.contact.phone_number)
    await _ask_description(message, state)


@dp.message(NewRequest.contact, F.text)
async def get_contact_text(message: Message, state: FSMContext) -> None:
    contact = message.text.strip()
    if len(contact) < 3:
        await message.answer("Контакт слишком короткий, попробуй ещё раз.")
        return
    await state.update_data(contact=contact)
    await _ask_description(message, state)


async def _ask_description(message: Message, state: FSMContext) -> None:
    await state.set_state(NewRequest.description)
    await message.answer(
        "Опиши задачу или вопрос как можно подробнее:",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(NewRequest.description, F.text)
async def get_description(message: Message, state: FSMContext) -> None:
    description = message.text.strip()
    if len(description) < 5:
        await message.answer("Опиши подробнее, пожалуйста (минимум несколько слов).")
        return

    data = await state.get_data()
    await state.clear()

    user = message.from_user
    request_id = db.create_request(
        user_id=user.id,
        username=user.username,
        category=data["category"],
        name=data["name"],
        contact=data["contact"],
        description=description,
    )

    # Автоответ пользователю
    await message.answer(
        f"✅ Заявка <b>#{request_id}</b> принята!\n\n"
        f"Категория: {CATEGORIES[data['category']]}\n"
        f"Имя: {data['name']}\n"
        f"Контакт: {data['contact']}\n\n"
        "Мы свяжемся с тобой в ближайшее время. "
        "Статус можно посмотреть в разделе «📋 Мои заявки».",
        reply_markup=main_menu(),
    )

    # Отправка в админ-чат
    uname = f"@{user.username}" if user.username else f"id{user.id}"
    admin_text = (
        f"📩 <b>Новая заявка #{request_id}</b>\n\n"
        f"Категория: {CATEGORIES[data['category']]}\n"
        f"Имя: {data['name']}\n"
        f"Контакт: {data['contact']}\n"
        f"От: {uname}\n\n"
        f"<b>Задача:</b>\n{description}\n\n"
        f"Статус: {db.STATUS_LABELS[db.STATUS_NEW]}"
    )
    try:
        await bot.send_message(
            ADMIN_CHAT_ID, admin_text, reply_markup=admin_status_kb(request_id)
        )
    except Exception as e:  # noqa: BLE001
        logging.error("Не удалось отправить заявку в админ-чат: %s", e)


# ─────────────────────────── Смена статуса (админ) ───────────────────────────
@dp.callback_query(F.data.startswith("st:"))
async def change_status(callback: CallbackQuery) -> None:
    _, rid_str, status = callback.data.split(":")
    request_id = int(rid_str)

    req = db.get_request(request_id)
    if req is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    db.set_status(request_id, status)
    label = db.STATUS_LABELS.get(status, status)

    # Обновляем сообщение в админ-чате
    base = callback.message.html_text
    if "Статус:" in base:
        base = base[: base.rfind("Статус:")].rstrip()
    new_admin_text = f"{base}\n\nСтатус: {label}"

    kb = admin_status_kb(request_id, with_status=(status != db.STATUS_DONE))
    await callback.message.edit_text(new_admin_text, reply_markup=kb)

    # Уведомляем пользователя об изменении статуса
    try:
        await bot.send_message(
            req["user_id"],
            f"🔔 Статус заявки <b>#{request_id}</b> изменён: {label}",
        )
    except Exception as e:  # noqa: BLE001
        logging.error("Не удалось уведомить пользователя: %s", e)

    await callback.answer(f"Статус: {label}")


# ─────────────────────────── Ответ клиенту (админ) ───────────────────────────
@dp.callback_query(F.data.startswith("reply:"))
async def cb_reply(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, callback.message.chat.id):
        await callback.answer("Доступно только администратору", show_alert=True)
        return

    request_id = int(callback.data.split(":", 1)[1])
    req = db.get_request(request_id)
    if req is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await state.set_state(AdminReply.message)
    await state.update_data(reply_request_id=request_id, reply_user_id=req["user_id"])
    await callback.message.answer(
        f"✍️ Напиши сообщение для клиента по заявке <b>#{request_id}</b> "
        f"({req['name']}). Оно уйдёт от лица бота.\n\n"
        "Отправь /cancel, чтобы отменить.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@dp.message(AdminReply.message, F.text)
async def admin_send_reply(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    user_id = data["reply_user_id"]
    request_id = data.get("reply_request_id")
    header = (
        f"💬 <b>Сообщение по заявке #{request_id}:</b>"
        if request_id
        else "💬 <b>Сообщение от менеджера:</b>"
    )
    where = f" по заявке #{request_id}" if request_id else ""
    try:
        await bot.send_message(user_id, f"{header}\n\n{message.text}")
        await message.answer(
            f"✅ Отправлено клиенту{where}.",
            reply_markup=main_menu(),
        )
    except Exception as e:  # noqa: BLE001
        await message.answer(
            f"⚠️ Не удалось отправить сообщение клиенту: {e}\n"
            "Возможно, пользователь заблокировал бота.",
            reply_markup=main_menu(),
        )


# ─────────── Входящие сообщения клиента → админу (двусторонний чат) ───────────
def dm_reply_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Ответить", callback_data=f"dm:{user_id}")]
        ]
    )


@dp.callback_query(F.data.startswith("dm:"))
async def cb_dm(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id, callback.message.chat.id):
        await callback.answer("Доступно только администратору", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])
    # подтягиваем последнюю заявку клиента для контекста (если есть)
    reqs = db.list_user_requests(user_id)
    request_id = reqs[0]["id"] if reqs else None

    await state.set_state(AdminReply.message)
    await state.update_data(reply_request_id=request_id, reply_user_id=user_id)
    await callback.message.answer(
        "✍️ Напиши ответ клиенту. Он уйдёт от лица бота.\n\n"
        "Отправь /cancel, чтобы отменить.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@dp.message(StateFilter(None), F.text, F.chat.type == "private")
async def client_incoming(message: Message) -> None:
    """Любое свободное сообщение клиента (вне сценария) пересылаем админу."""
    user = message.from_user
    # сообщения самого админа не пересылаем ему же
    if is_admin(user.id, message.chat.id):
        await message.answer(
            "Чтобы написать клиенту — используй кнопку «✉️ Написать клиенту» "
            "под заявкой. Меню ниже 👇",
            reply_markup=main_menu(),
        )
        return

    uname = f"@{user.username}" if user.username else f"id{user.id}"
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"💬 <b>Сообщение от клиента</b> ({user.full_name}, {uname}):\n\n{message.text}",
        reply_markup=dm_reply_kb(user.id),
    )
    await message.answer("✅ Сообщение передано менеджеру, скоро ответим.")


# ─────────────────────────── Запуск ───────────────────────────
async def main() -> None:
    db.init_db()
    logging.info("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
