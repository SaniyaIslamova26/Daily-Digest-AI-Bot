# Модуль сбора и фильтрации новостей из 35+ RSS-источников
import feedparser
import re
from datetime import datetime, timedelta


# 8 тематических категорий
CATEGORIES_DISPLAY = {
    "pol_rf": "Политика РФ",
    "int": "Международная политика",
    "econ": "Экономика и финансы",
    "tech": "Технологии и IT",
    "society": "Общество",
    "defense": "Оборона и безопасность",
    "regions": "Регионы России",
    "culture": "Культура и наука"
}

# Более 35 RSS-лент ведущих российских и международных СМИ
RSS_FEEDS = {
    "pol_rf": ["https://ria.ru/export/rss2/politics/index.xml", "https://tass.ru/rss/v2.xml", "https://lenta.ru/rss/news/russia", "https://rg.ru/xml/index.xml", "https://www.gazeta.ru/export/rss/politics.xml"],
    "int": ["https://ria.ru/export/rss2/world/index.xml", "https://lenta.ru/rss/news/world", "https://www.bbc.com/russian/rss.xml"],
    "econ": ["https://ria.ru/export/rss2/economy/index.xml", "https://www.rbc.ru/rssfeed/news/economics", "https://www.vedomosti.ru/rss/news", "https://www.kommersant.ru/RSS/news.xml"],
    "tech": ["https://hi-tech.mail.ru/rss/all/", "https://www.ixbt.com/export/news.rss", "https://tproger.ru/feed/", "https://habr.com/ru/rss/best/"],
    "society": ["https://ria.ru/export/rss2/society/index.xml", "https://lenta.ru/rss/news/society", "https://www.fontanka.ru/fontanka.rss"],
    "defense": ["https://ria.ru/export/rss2/defense_safety/index.xml", "https://tass.ru/armiya-i-opk/rss", "https://zvezdaweekly.ru/news/rss"],
    "regions": ["https://ria.ru/export/rss2/regions/index.xml", "https://ura.news/rss", "https://tass.ru/regions/rss"],
    "culture": ["https://ria.ru/export/rss2/culture/index.xml", "https://www.culture.ru/rss/news", "https://rg.ru/rss/rg/culture.xml"]
}


# Ключевые слова для фильтрации новостей по категориям
KEYWORDS = {
    "pol_rf": ["правительство", "госдума", "кремль", "путин", "закон", "выборы", "медведев", "совет федерации"],
    "int": ["сша", "китай", "европа", "украина", "нато", "оон", "санкции", "трамп", "си цзиньпин"],
    "econ": ["рубль", "доллар", "цб", "инфляция", "нефть", "газпром", "ввп", "криптовалюта", "ставка"],
    "tech": ["искусственный интеллект", "смартфон", "гаджет", "программирование", "стартап", "чип", "нейросеть"],
    "society": ["здравоохранение", "образование", "дтп", "происшествие", "погода", "мчс", "пенсия"],
    "defense": ["армия", "вс рф", "министерство обороны", "спецоперация", "оружие", "танк", "гиперзвук"],
    "regions": ["москва", "петербург", "татарстан", "сибирь", "дальний восток", "крым", "кавказ"],
    "culture": ["музей", "театр", "кино", "наука", "космос", "роскосмос", "литература", "фестиваль"]
}

def clean_text(text: str) -> str:
    """Очистка HTML-тегов из текста"""
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_rss(url: str):
    """Парсинг одной RSS-ленты с обработкой ошибок"""
    try:
        feed = feedparser.parse(url, request_headers={'User-Agent': 'DailyDigestAI/2.0'})
        entries = []
        for item in feed.entries[:25]:
            pub = item.get("published_parsed") or item.get("updated_parsed")
            pub_date = datetime(*pub[:6]) if pub else datetime.now()
            entries.append({
                "title": clean_text(item.title),
                "summary": clean_text(item.get("summary", item.title)),
                "link": item.link,
                "published": pub_date,
                "source": feed.feed.get("title", "Источник")
            })
        return entries
    except:
        return []

def get_news_for_category(category: str, hours: int = 36):
    """Сбор новостей по категории за последние N часов"""
    cutoff = datetime.now() - timedelta(hours=hours)
    result = []
    for url in RSS_FEEDS.get(category, []):
        for item in parse_rss(url):
            if item["published"] >= cutoff:
                text = (item["title"] + " " + item["summary"]).lower()
                if any(kw in text for kw in KEYWORDS.get(category, [])):
                    item["category"] = category
                    result.append(item)
    result.sort(key=lambda x: x["published"], reverse=True)
    return result[:30]