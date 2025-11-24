# Формирование персонализированного дайджеста
from datetime import datetime
from sources import get_news_for_category, CATEGORIES_DISPLAY


from functools import lru_cache
from datetime import datetime, timedelta

_last_cache_time = None
_last_digest_result = None

@lru_cache(maxsize=32)
def get_daily_digest_cached(categories_tuple):
    # превращаем список в кортеж, чтобы lru_cache работал
    return get_daily_digest(list(categories_tuple))

def get_daily_digest(categories):
    global _last_cache_time, _last_digest_result
    
    now = datetime.now()
    if _last_cache_time and (now - _last_cache_time).total_seconds() < 300:  # 5 минут
        if set(categories) == set(_last_digest_result[0]):
            return _last_digest_result[1]
    
    result = get_daily_digest_cached(tuple(sorted(categories)))
    
    _last_cache_time = now
    _last_digest_result = (categories, result)
    return result

def get_daily_digest(user_categories):
    all_news = []
    for cat in user_categories:
        all_news.extend(get_news_for_category(cat, hours=18))  # ← можно 12–24

    # Убираем дубликаты по ссылке, но сохраняем ВСЕ свежие новости
    seen = set()
    unique_news = []
    for news in all_news:
        if news["link"] not in seen:
            seen.add(news["link"])
            unique_news.append(news)

    # Сортируем по дате убывания (самые свежие сверху)
    unique_news.sort(key=lambda x: x["published"], reverse=True)

    # Берём ровно 12 самых свежих (или сколько есть)
    top_12 = unique_news[:12]

    # Формируем текст
    lines = [f"DailyDigest AI\n{datetime.now().strftime('%d.%m.%Y в %H:%M')} МСК\n"]
    for i, item in enumerate(top_12, 1):
        time_str = item["published"].strftime("%H:%M")
        lines.append(
            f"{i}. <b>{item['title']}</b>\n"
            f"{CATEGORIES_DISPLAY.get(item['category'], item['category'])} · {time_str} · {item['source']}\n"
            f"<a href='{item['link']}'>Читать полностью →</a>\n"
        )
    return "\n".join(lines)

