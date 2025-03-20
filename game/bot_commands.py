from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton
from aiogram.types import Message
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import FRONTEND_URL

router = Router()


@router.message(CommandStart())
async def command_start(message: Message):
    reply_markup = (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="Играть",
                web_app=WebAppInfo(url=FRONTEND_URL),
            ),
        )
        .as_markup()
    )

    await message.answer(
        text="Вступай в игру! 👇",
        reply_markup=reply_markup,
    )
