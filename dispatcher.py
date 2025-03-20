from aiogram import Dispatcher

from game import bot_commands

root_dispatcher = Dispatcher()
root_dispatcher.include_router(bot_commands.router)
