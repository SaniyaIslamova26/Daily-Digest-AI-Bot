# Формирование персонализированного дайджеста
from sources import get_news_for_category, CATEGORIES_DISPLAY
from datetime import datetime

def get_daily_digest(user_categories: list) -> str:
    """Генерация дайджеста из 12 главных новостей"""
    if not user_categories:
        return "Категории не выбраны. Используйте меню для подписки."

    all_news = []
    for cat in user_categories:
        all_news.extend(get_news_for_category(cat, hours=36))

    seen = set()
    unique = [n for n in all_news if n["link"] not in seen and not seen.add(n["link"])]
    unique.sort(key=lambda x: x["published"], reverse=True)

    top_news = unique[:12]

    lines = [f"DailyDigest AI\n{datetime.now().strftime('%d.%m.%Y в %H:%M')} МСК\n"]
    for i, item in enumerate(top_news, 1):
        cat_name = CATEGORIES_DISPLAY.get(item["category"], "Новости")
        time_str = item["published"].strftime("%H:%M")
        lines.append(
            f"{i}. <b>{item['title']}</b>\n"
            f"{cat_name} · {time_str} · {item['source']}\n"
            f"<a href='{item['link']}'>Читать полностью →</a>\n"
        )
    return "\n".join(lines)