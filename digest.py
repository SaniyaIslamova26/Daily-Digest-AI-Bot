# Формирование персонализированного дайджеста
# digest.py — супер-быстрая версия с кэшем и параллельным сбором
import asyncio
from datetime import datetime

# Кэш на 5 минут
_cache = {}
CACHE_TTL = 300

async def get_daily_digest(categories):
    if not categories:
        return "Вы не выбрали категории"

    key = tuple(sorted(categories))
    now = datetime.now()

    if key in _cache:
        text, ts = _cache[key]
        if (now - ts).total_seconds() < CACHE_TTL:
            return text + f"\n\n<i>Кэшировано {int((now - ts).total_seconds())} сек. назад</i>"

    from sources import get_news_for_category

    result = ["<b>DailyDigest AI — свежие новости</b>\n"]
    news_added = 0

    # Собираем ВСЁ параллельно — в 5–10 раз быстрее!
    tasks = [get_news_for_category[cat]() for cat in categories if cat in get_news_for_category]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for news_list in results:
        if isinstance(news_list, Exception) or not news_list:
            continue
        for title, link in news_list[:4]:  # по 4 новости с категории
            if news_added >= 12:
                break
            result.append(f"• <a href='{link}'>{title}</a>")
            news_added += 1
        if news_added >= 12:
            break

    if news_added == 0:
        result.append("Пока нет свежих новостей по вашим темам")

    final = "\n\n".join(result)
    _cache[key] = (final, now)
    return final


