import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from database.db import check_and_trigger_closure

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.datetime')
    async def test_closure_by_tickets(self, mock_datetime, mock_close, mock_is_closed, mock_count):
        # Setup: 2500 tickets, not closed, current date before deadline
        mock_count.return_value = 2500
        mock_is_closed.return_value = False
        mock_datetime.now.return_value = datetime(2025, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.datetime')
    async def test_no_closure(self, mock_datetime, mock_close, mock_is_closed, mock_count):
        # Setup: 100 tickets, not closed, before deadline
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_datetime.now.return_value = datetime(2025, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.datetime')
    async def test_closure_by_date(self, mock_datetime, mock_close, mock_is_closed, mock_count):
        # Setup: 100 tickets, not closed, current date is deadline
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_datetime.now.return_value = datetime(2026, 4, 10)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])
        self.assertIn("Время сбора билетов истекло", kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db._is_db_closed')
    @patch('database.db.close_collection')
    @patch('database.db.datetime')
    async def test_already_closed(self, mock_datetime, mock_close, mock_is_db_closed, mock_count):
        # Setup: 2500 tickets, already closed in DB
        mock_count.return_value = 2500
        mock_is_db_closed.return_value = True
        mock_datetime.now.return_value = datetime(2025, 1, 1)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
