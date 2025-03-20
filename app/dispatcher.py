from aiogram import Dispatcher

from app.game import bot_commands

root_dispatcher = Dispatcher()
root_dispatcher.include_router(bot_commands.router)
