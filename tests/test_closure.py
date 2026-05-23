import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from database.db import check_and_trigger_closure
import config

class TestClosure(unittest.IsolatedAsyncioTestCase):

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_get_count):
        # Setup
        mock_get_count.return_value = 3500
        mock_is_closed.return_value = False
        mock_bot = AsyncMock()

        # Execute
        await check_and_trigger_closure(mock_bot)

        # Verify
        mock_close.assert_called_once()
        mock_bot.send_message.assert_called_once()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_get_count):
        # Setup
        mock_get_count.return_value = 3499
        mock_is_closed.return_value = False
        mock_bot = AsyncMock()

        # Execute
        await check_and_trigger_closure(mock_bot)

        # Verify
        mock_close.assert_not_called()
        mock_bot.send_message.assert_not_called()

    @patch('database.db.is_collection_closed')
    @patch('database.db.get_total_tickets_count')
    async def test_already_closed(self, mock_get_count, mock_is_closed):
        # Setup
        mock_is_closed.return_value = True
        mock_get_count.return_value = 3501
        mock_bot = AsyncMock()

        # Execute
        await check_and_trigger_closure(mock_bot)

        # Verify
        mock_bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
