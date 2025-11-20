# Модуль работы с базой данных SQLite
import sqlite3
from datetime import datetime, timedelta
import json

DB_NAME = "daily_digest.db"

def init_db() -> None:
    """Инициализация структуры базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            categories TEXT DEFAULT '[]',
            subscribed INTEGER DEFAULT 1,
            referrer_id INTEGER DEFAULT 0,
            unlimited_until TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id: int) -> None:
    """Регистрация нового пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def update_categories(user_id: int, categories: list) -> None:
    """Сохранение выбранных пользователем категорий"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET categories = ? WHERE user_id = ?',
                   (json.dumps(categories), user_id))
    conn.commit()
    conn.close()

def get_user_categories(user_id: int) -> list:
    """Получение списка категорий пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT categories FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row and row[0] else []

def get_all_subscribers() -> list:
    """Список всех активных подписчиков"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE subscribed = 1')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def unsubscribe_user(user_id: int) -> None:
    """Отписка от рассылки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET subscribed = 0, categories = "[]" WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def set_unlimited(user_id: int, days: int = 7) -> None:
    """Активация безлимитного доступа на указанное количество дней"""
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET unlimited_until = ? WHERE user_id = ?', (expiry, user_id))
    conn.commit()
    conn.close()

def is_unlimited(user_id: int) -> bool:
    """Проверка наличия активного безлимитного доступа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT unlimited_until FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return datetime.fromisoformat(row[0]) > datetime.now()
    return False

def get_referrer(user_id: int) -> int:
    """Получение ID реферера пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0