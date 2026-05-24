import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.CONTEST_END_DATE', "2026-04-10")
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, date not reached
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False

        # Ensure current date is before CONTEST_END_DATE for this test
        # We'll use a fixed past date for the end date if needed, but let's just mock datetime.now
        with patch('database.db.datetime') as mock_datetime:
            mock_datetime.strptime.return_value = datetime(2026, 4, 10)
            mock_datetime.now.return_value = datetime(2026, 4, 1)

            bot = AsyncMock()
            await check_and_trigger_closure(bot)

            mock_close.assert_called_once()
            bot.send_message.assert_called_once()
            args, kwargs = bot.send_message.call_args
            self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])
            self.assertIn("достигли лимита", kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.CONTEST_END_DATE', "2026-04-10")
    async def test_closure_by_date(self, mock_close, mock_is_closed, mock_count):
        # Setup: few tickets, not closed, date passed
        mock_count.return_value = 100
        mock_is_closed.return_value = False

        with patch('database.db.datetime') as mock_datetime:
            mock_datetime.strptime.return_value = datetime(2026, 4, 10)
            mock_datetime.now.return_value = datetime(2026, 4, 11)

            bot = AsyncMock()
            await check_and_trigger_closure(bot)

            mock_close.assert_called_once()
            bot.send_message.assert_called_once()
            args, kwargs = bot.send_message.call_args
            self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])
            self.assertIn("Время приёма заявок истекло", kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.CONTEST_END_DATE', "2026-04-10")
    async def test_no_closure(self, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed, date not reached
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False

        with patch('database.db.datetime') as mock_datetime:
            mock_datetime.strptime.return_value = datetime(2026, 4, 10)
            mock_datetime.now.return_value = datetime(2026, 4, 1)

            bot = AsyncMock()
            await check_and_trigger_closure(bot)

            mock_close.assert_not_called()
            bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
