import asyncio
import os
from datetime import datetime, timedelta, timezone
from database.db import init_db, is_collection_closed, check_and_trigger_closure, DB_PATH
from config import COLLECTION_DEADLINE, TICKET_LIMIT
import aiosqlite
from unittest.mock import AsyncMock

async def test_closure_logic():
    # Setup: remove old test DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    await init_db()

    # 1. Test initially open
    assert not await is_collection_closed()

    # 2. Test deadline closure
    # We can't easily mock datetime.now() globally without a lot of ceremony,
    # but we can temporarily change the deadline in config or mock it.
    # Actually, is_collection_closed imports COLLECTION_DEADLINE from config.

    # Let's try mocking the TICKET_LIMIT or issuing many tickets to test limit closure.
    mock_bot = AsyncMock()

    # Manually insert 2500 tickets
    async with aiosqlite.connect(DB_PATH) as db:
        for i in range(1, 2501):
            await db.execute("INSERT INTO tickets (user_id, ticket_number, type) VALUES (?, ?, ?)", (1, i, 'base'))
        await db.commit()

    # check_and_trigger_closure should now close it
    closed = await check_and_trigger_closure(mock_bot)
    assert closed is True
    assert await is_collection_closed()
    mock_bot.send_message.assert_called_once()
    print("Ticket limit closure test: PASSED")

    # 3. Test deadline closure by setting deadline to past
    # Reset DB
    os.remove(DB_PATH)
    await init_db()

    # We need to monkeypatch config.COLLECTION_DEADLINE
    import config
    original_deadline = config.COLLECTION_DEADLINE
    config.COLLECTION_DEADLINE = datetime.now(timezone.utc) - timedelta(days=1)

    try:
        assert await is_collection_closed()
        print("Deadline closure test (is_collection_closed): PASSED")

        mock_bot_2 = AsyncMock()
        closed_again = await check_and_trigger_closure(mock_bot_2)
        assert closed_again is True
        mock_bot_2.send_message.assert_called_once()
        print("Deadline closure test (check_and_trigger_closure): PASSED")
    finally:
        config.COLLECTION_DEADLINE = original_deadline

if __name__ == "__main__":
    asyncio.run(test_closure_logic())
