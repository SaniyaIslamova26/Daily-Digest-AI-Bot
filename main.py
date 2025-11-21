# main.py — АБСОЛЮТНО ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ (Railway + aiogram 3.13+, ноябрь 2025)
import logging
import os                     # ← ЭТО БЫЛО ЗАБЫТО!
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update

import config
from db import init_db
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

# Бот и диспетчер
session = AiohttpSession(timeout=180.0)
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher()

# Подключаем все хендлеры (они сами зарегистрируются на dp)
from main_handlers import *

async def health(request):
    return web.Response(text="OK")

async def webhook(request):
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logging.error(f"Ошибка webhook: {e}")
        return web.Response(status=500)
    return web.Response()

async def on_startup(_):
    init_db()
    start_scheduler(bot)
    logging.info("DailyDigest AI ЗАПУЩЕН НАВСЕГДА — webhook работает, база в /data, всё идеально!")

app = web.Application()
app.router.add_get("/", health)
app.router.add_get("/health", health)
app.router.add_post("/webhook", webhook)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

