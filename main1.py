# main.py
# Основной модуль Telegram-бота DailyDigest AI
# Реализованы: персонализированная рассылка, реферальная система, расширенный сбор новостей


import logging
from aiohttp import web

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Update

import config
from db import init_db
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

session = AiohttpSession(timeout=180.0)
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = bot.dispatcher

# Хендлеры
from main_handlers import *

async def health(request):
    return web.Response(text="DailyDigest AI работает 24/7")

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
    logging.info("DailyDigest AI запущен на Railway — только webhook, polling отключён!")

app = web.Application()
app.router.add_get("/", health)
app.router.add_get("/health", health)
app.router.add_post("/webhook", webhook)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)