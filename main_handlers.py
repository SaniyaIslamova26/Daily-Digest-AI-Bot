# main_handlers.py — все обработчики бота (полная версия)



# main_handlers.py — финальная рабочая версия (с импортом dp)
from aiogram import types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import asyncio
from asyncio import wait_for, TimeoutError

# ← ЭТО ГЛАВНОЕ ДОБАВЛЕНИЕ: импортируем dp из main.py
from main import dp

from db import (
    add_user, update_categories, get_user_categories,
    get_all_subscribers, unsubscribe_user, set_unlimited
)
from digest import get_daily_digest
from sources import CATEGORIES_DISPLAY, get_news_for_category
import config

class Subscription(StatesGroup):
    choosing = State()

def main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Подписаться на новости"), KeyboardButton(text="Мои категории")],
        [KeyboardButton(text="Получить дайджест сейчас"), KeyboardButton(text="Ещё 10 новостей")],
        [KeyboardButton(text="Отписаться"), KeyboardButton(text="Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def categories_kb(selected: list) -> InlineKeyboardMarkup:
    kb = []
    for code, name in CATEGORIES_DISPLAY.items():
        mark = "✓" if code in selected else "⬜"
        kb.append([InlineKeyboardButton(text=f"{mark} {name}", callback_data=f"tog_{code}")])
    kb.append([InlineKeyboardButton(text="Готово — сохранить", callback_data="save")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== ВСЕ ХЕНДЛЕРЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    referrer_id = 0
    if args.startswith("ref_"):
        try:
            referrer_id = int(args[4:])
            if referrer_id != user_id and referrer_id > 10000:
                conn = sqlite3.connect("/data/daily_digest.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (referrer_id, user_id))
                conn.commit()
                conn.close()
                set_unlimited(user_id, days=7)
                set_unlimited(referrer_id, days=7)
                await message.answer("Реферальная ссылка активирована!\nВам и другу — безлимит на 7 дней!")
        except:
            pass

    add_user(user_id)
    ref_link = f"https://t.me/DailyDigestAI_Bot?start=ref_{user_id}"

    await message.answer(
        "DailyDigest AI\n\n"
        "Персональный политический дайджест из 35+ СМИ России\n\n"
        "• 8 тематических категорий\n"
        "• 12 главных новостей ежедневно\n"
        "• Безлимит по реферальной ссылке\n\n"
        f"Ваша ссылка:\n{ref_link}\n"
        "Пришлите другу — оба получите 7 дней без лимита!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Поделиться ссылкой", url=f"https://t.me/share/url?url={ref_link}")
        ]])
    )
    await message.answer("Выберите категории:", reply_markup=main_keyboard())

@dp.message(lambda m: m.text == "Подписаться на новости")
async def subscribe_start(message: types.Message, state: FSMContext):
    current = get_user_categories(message.from_user.id)
    await state.set_state(Subscription.choosing)
    await state.update_data(selected=current)
    await message.answer("Отметьте интересующие темы:", reply_markup=categories_kb(current))

@dp.callback_query(lambda c: c.data.startswith("tog_"))
async def toggle_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data[4:]
    data = await state.get_data()
    selected = data.get("selected", [])
    if cat in selected:
        selected.remove(cat)
    else:
        selected.append(cat)
    await state.update_data(selected=selected)
    await callback.message.edit_reply_markup(reply_markup=categories_kb(selected))
    await callback.answer()

@dp.callback_query(lambda c: c.data == "save")
async def save_categories(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])
    update_categories(callback.from_user.id, selected)
    await state.clear()

    names = [CATEGORIES_DISPLAY.get(c, c) for c in selected]
    text = "Подписка сохранена!\nВаши темы:\n• " + "\n• ".join(names) if names else "Подписка сохранена (тем пока нет)"

    await callback.message.edit_text(f"{text}\n\nЕжедневно в 9:00 МСК — свежий дайджест")
    await callback.message.answer("Готово!", reply_markup=main_keyboard())
    await callback.answer("Сохранено")


@dp.message(lambda m: m.text == "Мои категории")
async def my_categories(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    names = [CATEGORIES_DISPLAY.get(c, c) for c in cats]
    text = "Ваши категории:\n• " + "\n• ".join(names) if names else "Категории не выбраны"
    await message.answer(text)


@dp.message(lambda m: m.text == "Получить дайджест сейчас")
async def manual_digest(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    if not cats:
        await message.answer("Сначала выберите категории")
        return

    await message.answer("Формирую дайджест (макс. 20 сек)…")

    try:
        # ← Теперь БЕЗ to_thread — просто await, потому что get_daily_digest уже async!
        digest_text = await asyncio.wait_for(get_daily_digest(cats), timeout=20)
        
        await message.answer(
            digest_text or "Новостей по вашим категориям пока нет 🤷‍♂️",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except asyncio.TimeoutError:
        await message.answer(
            "Дайджест формируется слишком долго (более 20 сек).\n"
            "Попробуйте позже или выберите меньше категорий."
        )
    except Exception as e:
        logging.error(f"Ошибка дайджеста: {e}")
        await message.answer("Произошла ошибка при сборе новостей")
@dp.message(lambda m: m.text == "Ещё 10 новостей")
async def more_news(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    if not cats:
        await message.answer("Сначала выберите категории")
        return

    all_news = []
    for cat in cats:
        all_news.extend(get_news_for_category(cat, hours=36))

    seen = set()
    unique = [n for n in all_news if n["link"] not in seen and not seen.add(n["link"])]
    unique.sort(key=lambda x: x["published"], reverse=True)
    extra = unique[12:22]

    if not extra:
        await message.answer("Больше новостей пока нет")
        return

    lines = ["Ещё 10 новостей:\n"]
    for i, item in enumerate(extra, 13):
        lines.append(
            f"{i}. <b>{item['title']}</b>\n"
            f"{CATEGORIES_DISPLAY.get(item['category'], 'Новости')} · {item['source']}\n"
            f"<a href='{item['link']}'>Читать →</a>\n"
        )
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@dp.message(lambda m: m.text == "Отписаться")
async def unsubscribe(message: types.Message):
    unsubscribe_user(message.from_user.id)
    await message.answer("Вы отписаны. Вернуться — /start")


@dp.message(lambda m: m.text == "Статистика")
async def stats(message: types.Message):
    await message.answer(f"DailyDigest AI читают {len(get_all_subscribers())} человек")


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    await message.answer(
        f"Админ-панель\nПодписчиков: {len(get_all_subscribers())}\nРассылка: 9:00 МСК",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Принудительная рассылка", callback_data="force_send")]])
    )


@dp.callback_query(lambda c: c.data == "force_send")
async def force_send(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        return
    await callback.message.edit_text("Рассылка запущена...")
    from scheduler import send_daily_digest
    await send_daily_digest(bot)

    await callback.message.edit_text("Рассылка завершена")








