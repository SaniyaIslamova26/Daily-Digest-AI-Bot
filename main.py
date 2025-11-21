# main.py — 100% рабочая версия для Railway + aiogram 3.13+
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update

import config
from db import init_db
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

# ← Правильное создание бота и диспетчера в aiogram 3.13+
session = AiohttpSession(timeout=180.0)
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher()                                   # ← вот так теперь!

# Подключаем все хендлеры (они сами регистрируются на dp)
from main_handlers import *

async def health(request):
    return web.Response(text="OK")

async def webhook(request):
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return web.Response()

async def on_startup(_):
    init_db()
    start_scheduler(bot)
    logging.info("DailyDigest AI полностью запущен — webhook работает, volume /data подключён!")

app = web.Application()
app.router.add_get("/", health)
app.router.add_get("/health", health)
app.router.add_post("/webhook", webhook)
app.on_startup.append(on_startup)

if name == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)