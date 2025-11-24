# main_handlers.py — все хендлеры + защита от зависаний
from aiogram import types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import sqlite3
import logging
import asyncio

from main import dp
from db import (
    add_user, update_categories, get_user_categories,
    get_all_subscribers, unsubscribe_user, set_unlimited
)
from digest import get_daily_digest
from sources import CATEGORIES_DISPLAY
import config

class Subscription(StatesGroup):
    choosing = State()

def main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Подписаться на новости"), KeyboardButton(text="Мои категории")],
        [KeyboardButton(text="Получить дайджест сейчас"), KeyboardButton(text="Статистика")],
        [KeyboardButton(text="Отписаться")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def categories_kb(selected: list) -> InlineKeyboardMarkup:
    kb = []
    for code, name in CATEGORIES_DISPLAY.items():
        mark = "✓" if code in selected else "⬜"
        kb.append([InlineKeyboardButton(text=f"{mark} {name}", callback_data=f"tog_{code}")])
    kb.append([InlineKeyboardButton(text="Готово — сохранить", callback_data="save")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        "DailyDigest AI\n\nЕжедневно в 9:00 МСК — свежий дайджест из 35+ СМИ\n"
        "8 тематических категорий • 12 главных новостей\n\nВыберите категории:",
        reply_markup=main_keyboard()
    )
    current = get_user_categories(message.from_user.id)
    await message.answer("Отметьте интересующие темы:", reply_markup=categories_kb(current))

@dp.message(lambda m: m.text == "Подписаться на новости")
async def subscribe_start(message: types.Message, state: FSMContext):
    current = get_user_categories(message.from_user.id)
    await state.set_state(Subscription.choosing)
    await message.answer("Выберите категории:", reply_markup=categories_kb(current))

@dp.callback_query(lambda c: c.data and c.data.startswith("tog_"))
async def toggle_category(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data[4:]
    data = await state.get_data()
    selected = data.get("selected", get_user_categories(callback.from_user.id))
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
    text = "Подписка сохранена!\nВаши темы:\n• " + "\n• ".join(names) if names else "Вы отписаны от категорий"
    await callback.message.edit_text(text, reply_markup=main_keyboard())
    await callback.answer("Готово!")

@dp.message(lambda m: m.text == "Мои категории")
async def my_categories(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    names = [CATEGORIES_DISPLAY.get(c, c) for c in cats]
    text = "Ваши категории:\n• " + "\n• ".join(names) if names else "Не выбраны"
    await message.answer(text, reply_markup=main_keyboard())

@dp.message(lambda m: m.text == "Получить дайджест сейчас")
async def manual_digest(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    if not cats:
        await message.answer("Сначала выберите категории")
        return

    msg = await message.answer("Формирую дайджест… (макс. 18 сек)")

    try:
        digest = await asyncio.wait_for(get_daily_digest(cats), timeout=18)
        await msg.edit_text(digest or "Новостей пока нет", parse_mode="HTML", disable_web_page_preview=True)
    except asyncio.TimeoutError:
        await msg.edit_text("Источники слишком медленно отвечают.\nПопробуйте через 5–10 минут или уменьшите количество категорий.")

@dp.message(lambda m: m.text == "Статистика")
async def stats(message: types.Message):
    await message.answer(f"Подписчиков: {len(get_all_subscribers())}")

@dp.message(lambda m: m.text == "Отписаться")
async def unsubscribe(message: types.Message):
    unsubscribe_user(message.from_user.id)
    await message.answer("Вы отписаны. Вернуться — /start")








