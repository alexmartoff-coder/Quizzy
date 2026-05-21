import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date
from database.db import check_and_trigger_closure

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count):
        # Setup: 2500 tickets, not closed
        mock_count.return_value = 2500
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])
        self.assertIn("2500", kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.date')
    async def test_no_closure(self, mock_date, mock_close, mock_is_closed, mock_count):
        # Setup: 100 tickets, not closed, before deadline
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_date.today.return_value = date(2025, 1, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.date')
    async def test_closure_by_date(self, mock_date, mock_close, mock_is_closed, mock_count):
        # Setup: 100 tickets, not closed, after deadline
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_date.today.return_value = date(2026, 4, 11)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed, mock_count):
        # Setup: 2500 tickets, already closed
        mock_count.return_value = 2500
        mock_is_closed.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
