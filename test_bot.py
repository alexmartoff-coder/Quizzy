import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from database.db import init_db, add_user, get_next_ticket_id, get_total_tickets_count, is_collection_closed, DB_PATH
import os

class TestBotLogic(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Use a separate test database
        self.db_path = "test_bot_database.db"
        with patch("database.db.DB_PATH", self.db_path):
            await init_db()

    async def asyncTearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    async def test_ticket_increment(self):
        with patch("database.db.DB_PATH", self.db_path):
            from database.db import increment_ticket_id
            start_id = await increment_ticket_id(5)
            self.assertEqual(start_id, 1)
            next_id = await get_next_ticket_id()
            self.assertEqual(next_id, 6)

    async def test_user_and_tickets(self):
        with patch("database.db.DB_PATH", self.db_path):
            from database.db import add_ticket, get_user_tickets
            await add_user(123, "testuser", "Test User")
            await add_ticket(123, 1, "base")
            await add_ticket(123, 2, "bonus")

            tickets = await get_user_tickets(123)
            self.assertEqual(tickets, [1, 2])

            total = await get_total_tickets_count()
            self.assertEqual(total, 2)

    async def test_collection_closure(self):
        with patch("database.db.DB_PATH", self.db_path):
            from database.db import close_collection
            self.assertFalse(await is_collection_closed())
            await close_collection()
            self.assertTrue(await is_collection_closed())

    @patch("aiogram.Bot")
    async def test_quiz_completion_logic(self, MockBot):
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        mock_bot_instance.session = MagicMock()
        mock_bot_instance.session.close = AsyncMock()

        with patch("database.db.DB_PATH", self.db_path):
            from handlers.quiz import finish_quiz_logic
            from database.db import set_quiz_session, get_user_tickets

            user_id = 456
            await add_user(user_id, "quizzer", "Quizzer")
            # Mock session with 10 correct answers
            await set_quiz_session(user_id, score=10, current_question=10, is_active=True)

            mock_state = AsyncMock()
            mock_state.get_data = AsyncMock(return_value={})

            # Mock TICKET_LIMIT to 2 for testing closure
            with patch("handlers.quiz.TICKET_LIMIT", 2):
                await finish_quiz_logic(mock_bot_instance, mock_state, user_id)

            tickets = await get_user_tickets(user_id)
            # 3 bonus tickets for score 10
            self.assertEqual(len(tickets), 3)

            # Check if closed
            self.assertTrue(await is_collection_closed())

            # Check if channel announcement was attempted
            mock_bot_instance.send_message.assert_any_call(
                chat_id="@mozgo_boy",
                text=unittest.mock.ANY
            )

if __name__ == "__main__":
    unittest.main()
