import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Dispatcher, Bot
from aiogram.types import Message, User, Chat
from datetime import datetime

class TestRulesHandler(unittest.IsolatedAsyncioTestCase):
    async def test_rules_trigger(self):
        # Create a mock message
        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=123, type="private")
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=chat,
            from_user=user,
            text="📜 Правила розыгрыша"
        )
        message.bot = MagicMock(spec=Bot)
        message.answer = AsyncMock()

        # Call the handler directly
        from handlers.base import cmd_rules
        await cmd_rules(message)

        # Verify answer was called with rules text
        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        self.assertIn("Правила розыгрыша iPhone 17", args[0])
        # Markdown V1 is what we use in handlers/base.py
        self.assertEqual(kwargs.get("parse_mode"), "Markdown")

if __name__ == "__main__":
    unittest.main()
