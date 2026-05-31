import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from database.db import check_and_trigger_closure, is_collection_closed
from config import TICKET_LIMIT, CONTEST_DEADLINE

class TestClosure(unittest.IsolatedAsyncioTestCase):

    @patch('database.db.get_paid_tickets_count')
    @patch('database.db.get_moscow_now')
    @patch('database.db.aiosqlite.connect')
    async def test_is_collection_closed_logic(self, mock_db, mock_now, mock_count):
        # Test 1: Below limit and before deadline
        mock_count.return_value = TICKET_LIMIT - 1
        mock_now.return_value = CONTEST_DEADLINE.replace(year=2025)

        # Mock DB for settings 'is_closed'
        mock_conn = MagicMock()
        mock_db.return_value.__aenter__.return_value = mock_conn

        mock_cursor = AsyncMock()
        mock_conn.execute.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('0',)

        closed = await is_collection_closed()
        self.assertFalse(closed)

        # Test 2: Reach limit
        mock_count.return_value = TICKET_LIMIT
        closed = await is_collection_closed()
        self.assertTrue(closed)

        # Test 3: Past deadline
        mock_count.return_value = 0
        mock_now.return_value = CONTEST_DEADLINE.replace(year=2027)
        closed = await is_collection_closed()
        self.assertTrue(closed)

    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.aiosqlite.connect')
    async def test_check_and_trigger_closure(self, mock_db, mock_close, mock_is_closed):
        bot = AsyncMock()

        # Setup: already closed in settings
        mock_is_closed.return_value = True
        mock_conn = MagicMock()
        mock_db.return_value.__aenter__.return_value = mock_conn

        mock_cursor = AsyncMock()
        mock_conn.execute.return_value.__aenter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('1',) # settings says is_closed=1

        await check_and_trigger_closure(bot)
        mock_close.assert_not_called()

        # Setup: should trigger (is_collection_closed returns True, but settings says 0)
        mock_is_closed.return_value = True
        mock_cursor.fetchone.return_value = ('0',) # settings says is_closed=0

        # Reset mocks for the next part
        mock_close.reset_mock()

        # Mock for broadcast_closure_to_all
        mock_cursor.fetchall.return_value = [] # No users to broadcast to

        await check_and_trigger_closure(bot)
        mock_close.assert_called_once()
        bot.send_message.assert_called() # Should send to channel

if __name__ == '__main__':
    unittest.main()
