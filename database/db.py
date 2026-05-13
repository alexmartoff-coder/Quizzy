import aiosqlite
import os
from datetime import datetime

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

        # Initialize next_ticket_id if not exists
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('next_ticket_id', '1')")
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('is_closed', '0')")
        await db.commit()

async def get_next_ticket_id():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'next_ticket_id'") as cursor:
            row = await cursor.fetchone()
            return int(row[0])

async def increment_ticket_id(count=1):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'next_ticket_id'") as cursor:
            row = await cursor.fetchone()
            current_id = int(row[0])
            new_id = current_id + count
            await db.execute("UPDATE settings SET value = ? WHERE key = 'next_ticket_id'", (str(new_id),))
            await db.commit()
            return current_id # Returns the starting ID for the tickets just issued

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

async def get_leaderboard(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        # Leaderboard based on number of tickets
        async with db.execute("""
            SELECT u.username, u.full_name, COUNT(t.id) as ticket_count
            FROM users u
            JOIN tickets t ON u.user_id = t.user_id
            GROUP BY u.user_id
            ORDER BY ticket_count DESC
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
