import json
import traceback
import uuid
from contextlib import contextmanager
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Callable

import structlog
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

if TYPE_CHECKING:
    from app.patches import Bot

logger = structlog.stdlib.get_logger()


def generate_referral_code() -> str:
    return uuid.uuid4().hex[:10]


def struct_log(event: str, special_logger: Callable = None, **kwargs) -> None:
    payload = dict(event=event, payload=kwargs)

    try:
        log = json.dumps(payload)
    except TypeError:
        log = payload

    if special_logger:
        special_logger(log)
    else:
        logger.info(log)


@contextmanager
def suppress() -> None:
    try:
        yield
    except Exception as e:
        logger.error("Error has occurred", exception=traceback.format_exception(e))


def format_value(value: str | float | int | Decimal) -> str | float | int | Decimal:
    try:
        if not isinstance(value, (str, float, int, Decimal)):
            return value

        formatted_value = str(
            Decimal(str(float(value))).quantize(
                Decimal("1.11"),
                rounding=ROUND_HALF_UP,
            )
        ).replace(".", ",")

        # Разделяем целую и дробную части
        integer_part, decimal_part = formatted_value.rsplit(",", 1)

        # Добавляем пробелы между разрядами
        integer_part_with_spaces = f"{int(integer_part):,}".replace(",", " ")

        # Собираем окончательный результат
        formatted_value_with_spaces = f"{integer_part_with_spaces},{decimal_part}".replace(",", ".")
        return formatted_value_with_spaces
    except Exception:  # noqa
        return value


def chunk_list(lst: list, size: int) -> list[list]:
    return [lst[i : i + size] for i in range(0, len(lst), size)]


async def safe_delete(message: Message | CallbackQuery | int, bot: "Bot" = None) -> None:
    try:
        if isinstance(message, Message):
            await message.delete()

        if isinstance(message, CallbackQuery):
            await message.message.delete()

        if isinstance(message, int):
            await bot.delete_message(chat_id=message, message_id=message)

    except TelegramBadRequest:
        pass


async def safe_answer(message: Message | CallbackQuery | int) -> None:
    try:
        await message.answer()
    except TelegramBadRequest:
        pass
