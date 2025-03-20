import asyncio
import datetime
import hashlib
import hmac
import json
import os
import secrets
from contextlib import asynccontextmanager
from enum import Enum
from operator import itemgetter
from typing import Any, Dict
from urllib.parse import parse_qsl

import structlog
from aiogram import Bot as _Bot
from aiogram.client.default import Default
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InputFile, TelegramObject
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from starlette import status

from config import AUTH_CHECK_TELEGRAM_TOKEN
from config import TELEGRAM_BOT_TOKEN
from config import TELEGRAM_BOT_WEBHOOK_HOST
from config import TELEGRAM_BOT_WEBHOOK_SECRET

logger = structlog.stdlib.get_logger()


class WebappData(BaseModel):
    telegram_id: int
    language_code: str | None = Field(default="en")
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_premium: bool | None = None
    photo_url: str | None = None
    start_param: str | None = None


class Bot(_Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def _setup_webhook(self) -> None:
        try:
            logger.info(f"Setting webhook for bot {self.id=}; {TELEGRAM_BOT_WEBHOOK_HOST=}")
            random = os.urandom(5).hex()
            await self.set_webhook(
                max_connections=100,
                url=f"{TELEGRAM_BOT_WEBHOOK_HOST}/api/v1/telegram?r={random}",
                secret_token=TELEGRAM_BOT_WEBHOOK_SECRET,
            )
        except TelegramRetryAfter as e:
            logger.info(f"Retrying webhook after {e.retry_after} for bot {self.id=}, {e=}")
            await asyncio.sleep(e.retry_after)
            await self._setup_webhook()

    @asynccontextmanager
    async def setup(self, app: FastAPI) -> None:  # noqa
        await self._setup_webhook()
        yield

    def auth_webapp(self, webapp_data: str) -> WebappData:
        parsed_data = dict(parse_qsl(webapp_data))

        try:
            param_hash = parsed_data.pop("hash")
            max_auth_date = datetime.datetime.fromtimestamp(int(parsed_data["auth_date"])) + datetime.timedelta(days=7)
        except KeyError:
            raise HTTPException(detail="invalid webapp data", status_code=status.HTTP_401_UNAUTHORIZED)

        if datetime.datetime.utcnow() > max_auth_date:  # noqa
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth_date is too old")

        sorted_data = sorted(parsed_data.items(), key=itemgetter(0))
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_data)

        secret_key = hmac.new(key=b"WebAppData", msg=self.token.encode(), digestmod=hashlib.sha256)
        actual_hash = hmac.new(
            key=secret_key.digest(),
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        invalid_hash = (param_hash != actual_hash) and AUTH_CHECK_TELEGRAM_TOKEN

        if invalid_hash:
            raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail="hash mismatch")

        user_data = json.loads(parsed_data["user"])

        return WebappData(
            telegram_id=user_data["id"],
            language_code=user_data.get("language_code"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            username=user_data.get("username"),
            is_premium=user_data.get("is_premium"),
            start_param=parsed_data.get("start_param"),
        )


def prepare_value(value: Any, bot: Bot, files: Dict[str, Any], _dumps_json: bool = True) -> Any:  # noqa
    """
    from aiogram.client.session.aiohttp.BaseSession
    """

    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Default):
        default_value = bot.default[value.name]
        return prepare_value(default_value, bot=bot, files=files, _dumps_json=_dumps_json)
    if isinstance(value, InputFile):
        key = secrets.token_urlsafe(10)
        files[key] = value
        return f"attach://{key}"
    if isinstance(value, dict):
        value = {
            key: prepared_item
            for key, item in value.items()
            if (prepared_item := prepare_value(item, bot=bot, files=files, _dumps_json=False)) is not None
        }
        if _dumps_json:
            return json.dumps(value)
        return value
    if isinstance(value, list):
        value = [
            prepared_item
            for item in value
            if (prepared_item := prepare_value(item, bot=bot, files=files, _dumps_json=False)) is not None
        ]
        if _dumps_json:
            return json.dumps(value)
        return value
    if isinstance(value, datetime.timedelta):
        now = datetime.datetime.now()
        return str(round((now + value).timestamp()))
    if isinstance(value, datetime.datetime):
        return str(round(value.timestamp()))
    if isinstance(value, Enum):
        return prepare_value(value.value, bot=bot, files=files)
    if isinstance(value, TelegramObject):
        return prepare_value(
            value.model_dump(warnings=False),
            bot=bot,
            files=files,
            _dumps_json=_dumps_json,
        )

    if _dumps_json:
        return json.dumps(value)

    return value


bot = Bot(token=TELEGRAM_BOT_TOKEN)
