import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User
from handlers.base import cmd_rules

class TestBaseHandlers(unittest.IsolatedAsyncioTestCase):
    async def test_cmd_rules(self):
        # Setup mock message
        chat = Chat(id=123, type="private")
        user = User(id=123, is_bot=False, first_name="Test")
        message = MagicMock(spec=Message)
        message.chat = chat
        message.from_user = user
        message.answer = AsyncMock()

        # Execute
        await cmd_rules(message)

        # Verify
        message.answer.assert_called_once()
        args, kwargs = message.answer.call_args
        self.assertIn("Правила розыгрыша iPhone 17", args[0])
        self.assertEqual(kwargs.get("parse_mode"), "HTML")

if __name__ == "__main__":
    asyncio.run(unittest.main())
