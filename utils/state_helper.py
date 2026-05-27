from aiogram import Bot
from aiogram.fsm.context import FSMContext

_dp = None

def set_dp(dp):
    global _dp
    _dp = dp

async def get_state(bot: Bot, user_id: int) -> FSMContext:
    if _dp is None:
        return None
    return _dp.fsm.get_context(bot, user_id, user_id)
