import aiosqlite
import os
from datetime import datetime
from aiogram import Bot
from config import TICKET_LIMIT, CHANNEL_ID

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticket_number INTEGER,
                type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_seen_questions (
                user_id INTEGER,
                question_id INTEGER,
                PRIMARY KEY (user_id, question_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                user_id INTEGER PRIMARY KEY,
                score INTEGER DEFAULT 0,
                current_question INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # YOOKASSA PAYMENT INTEGRATION
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                payload TEXT,
                telegram_payment_charge_id TEXT,
                provider_payment_charge_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)

        # Таблица доступных номеров для рандомной выдачи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS available_tickets (
                ticket_number INTEGER PRIMARY KEY
            )
        """)

        # Инициализация настроек
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('is_closed', '0')")

        # Пополнение пула билетов, если он пуст и мы еще не начали выдачу
        async with db.execute("SELECT COUNT(*) FROM tickets") as cursor:
            issued_count = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM available_tickets") as cursor:
            available_count = (await cursor.fetchone())[0]

        if issued_count == 0 and available_count == 0:
            # Заполняем пул номерами 1-3500
            for i in range(1, 3501):
                await db.execute("INSERT INTO available_tickets (ticket_number) VALUES (?)", (i,))

        await db.commit()

async def issue_random_tickets(user_id, count, ticket_type):
    """Выдает указанное количество случайных билетов пользователю."""
    issued_tickets = []
    async with aiosqlite.connect(DB_PATH) as db:
        for _ in range(count):
            # Выбираем случайный билет из доступных
            async with db.execute("SELECT ticket_number FROM available_tickets ORDER BY RANDOM() LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    ticket_num = row[0]
                    # Удаляем из доступных
                    await db.execute("DELETE FROM available_tickets WHERE ticket_number = ?", (ticket_num,))
                    # Добавляем пользователю
                    await db.execute("INSERT INTO tickets (user_id, ticket_number, type) VALUES (?, ?, ?)",
                                     (user_id, ticket_num, ticket_type))
                    issued_tickets.append(ticket_num)
        await db.commit()
    return issued_tickets

async def get_next_ticket_id():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'next_ticket_id'") as cursor:
            row = await cursor.fetchone()
            return int(row[0])


async def add_user(user_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                         (user_id, username, full_name))
        await db.commit()

async def add_ticket(user_id, ticket_number, ticket_type):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO tickets (user_id, ticket_number, type) VALUES (?, ?, ?)",
                         (user_id, ticket_number, ticket_type))
        await db.commit()

async def get_user_tickets(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number FROM tickets WHERE user_id = ? ORDER BY ticket_number", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_total_tickets_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM tickets") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def set_quiz_session(user_id, score=0, current_question=0, is_active=True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO quiz_sessions (user_id, score, current_question, is_active)
            VALUES (?, ?, ?, ?)
        """, (user_id, score, current_question, is_active))
        await db.commit()

async def get_quiz_session(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT score, current_question, is_active FROM quiz_sessions WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_quiz_score(user_id, score):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE quiz_sessions SET score = ? WHERE user_id = ?", (score, user_id))
        await db.commit()

async def update_quiz_question(user_id, current_question):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE quiz_sessions SET current_question = ? WHERE user_id = ?", (current_question, user_id))
        await db.commit()

async def finish_quiz_session(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE quiz_sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_leaderboard(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        # Leaderboard based on number of tickets (base + bonus)
        async with db.execute("""
            SELECT
                u.username,
                u.full_name,
                COUNT(t.id) as total_count,
                SUM(CASE WHEN t.type = 'base' THEN 1 ELSE 0 END) as base_count,
                SUM(CASE WHEN t.type = 'bonus' THEN 1 ELSE 0 END) as bonus_count
            FROM users u
            JOIN tickets t ON u.user_id = t.user_id
            GROUP BY u.user_id
            ORDER BY total_count DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()

async def is_collection_closed():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'is_closed'") as cursor:
            row = await cursor.fetchone()
            return row[0] == '1'

async def close_collection():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE settings SET value = '1' WHERE key = 'is_closed'")
        await db.commit()

async def get_user_seen_question_ids(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT question_id FROM user_seen_questions WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def mark_questions_as_seen(user_id, question_ids):
    async with aiosqlite.connect(DB_PATH) as db:
        for q_id in question_ids:
            await db.execute("INSERT OR IGNORE INTO user_seen_questions (user_id, question_id) VALUES (?, ?)",
                             (user_id, q_id))
        await db.commit()

async def clear_user_seen_questions(user_id):
    """Сброс увиденных вопросов (например, если пул закончился)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_seen_questions WHERE user_id = ?", (user_id,))
        await db.commit()

# YOOKASSA PAYMENT INTEGRATION
async def log_payment(user_id, amount, payload, telegram_id, provider_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO payments (user_id, amount, payload, telegram_payment_charge_id, provider_payment_charge_id)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, amount, payload, telegram_id, provider_id))
        await db.commit()

async def check_and_trigger_closure(bot: Bot):
    """Проверяет условия закрытия и выполняет действия по закрытию."""
    total = await get_total_tickets_count()

    if total >= TICKET_LIMIT and not await is_collection_closed():
        await close_collection()
        try:
            text = (
                "🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                "Мы достигли лимита в 3500 билетов.\n"
                "Спасибо всем, кто принял участие!\n\n"
                "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
            )
            await bot.send_message(chat_id=CHANNEL_ID, text=text)
        except Exception as e:
            import logging
            logging.error(f"Error sending closure message to channel: {e}")
