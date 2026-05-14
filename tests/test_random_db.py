import asyncio
from database.db import init_db, issue_random_tickets, get_user_tickets, get_total_tickets_count
import os

async def test_random_issuance():
    if os.path.exists("bot_database.db"):
        os.remove("bot_database.db")

    await init_db()

    # Issue 1 ticket
    user1 = 101
    issued1 = await issue_random_tickets(user1, 1, "base")
    print(f"User 101 issued: {issued1}")

    # Issue 3 tickets
    user2 = 102
    issued2 = await issue_random_tickets(user2, 3, "bonus")
    print(f"User 102 issued: {issued2}")

    tickets1 = await get_user_tickets(user1)
    tickets2 = await get_user_tickets(user2)

    print(f"DB User 101: {tickets1}")
    print(f"DB User 102: {tickets2}")

    total = await get_total_tickets_count()
    print(f"Total tickets: {total}")

if __name__ == "__main__":
    asyncio.run(test_random_issuance())
