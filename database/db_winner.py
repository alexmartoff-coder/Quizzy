import aiosqlite
from database.db import DB_PATH

async def get_preliminary_winner():
    async with aiosqlite.connect(DB_PATH) as db:
        # Наибольший балл, затем наименьшее время
        query = """
            SELECT ticket_number, user_id, score, total_time
            FROM final_results
            WHERE is_mini_quiz = 0
            ORDER BY score DESC, total_time ASC
            LIMIT 1
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchone()

async def check_for_ties():
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT ticket_number, user_id, score, total_time
            FROM final_results
            WHERE score = (SELECT MAX(score) FROM final_results)
            AND total_time = (SELECT MIN(total_time) FROM final_results WHERE score = (SELECT MAX(score) FROM final_results))
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return rows if len(rows) > 1 else None

async def setup_mini_quiz(tickets):
    # logic to notify users and prepare for mini-quiz
    pass
