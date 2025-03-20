from aiogram import F
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, Message, WebAppInfo
from aiogram.types import PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import insert_webapp_data
from app.patches import WebappData
from config import FRONTEND_URL

router = Router()


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    await insert_webapp_data(
        data=WebappData(
            telegram_id=message.from_user.id,
            language_code=message.from_user.language_code,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            is_premium=message.from_user.is_premium,
        )
    )

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


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    user_id = int(payment.invoice_payload)

