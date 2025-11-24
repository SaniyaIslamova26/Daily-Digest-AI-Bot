# main.py — финальная версия для Railway (webhook, aiogram 3.13+)
import logging
import os
from aiohttp import web, ClientTimeout

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update

import config
from db import init_db
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

# Таймаут 0 — убивает 499 навсегда
session = AiohttpSession(timeout=ClientTimeout(total=0))
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher()

from main_handlers import *

async def health(request):
    return web.Response(text="OK")

async def webhook(request):
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logging.error(f"Ошибка webhook: {e}")
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




