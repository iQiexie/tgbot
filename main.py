from contextlib import asynccontextmanager
from typing import Annotated, Any

from aiogram.methods import TelegramMethod
from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from fastapi.security import APIKeyHeader
from starlette import status

from config import TELEGRAM_BOT_WEBHOOK_SECRET
from db import init_db
from dispatcher import root_dispatcher
from game import endpoints
from patches import bot, prepare_value
from utils import struct_log

router = APIRouter(tags=["Telegram callback"], prefix="/api/v1")
telegram_auth_header = APIKeyHeader(
    name="X-Telegram-Bot-Api-Secret-Token",
    scheme_name="AuthTelegram",
    auto_error=True,
)


def auth_telegram(token: str = Depends(telegram_auth_header)) -> bool:
    if token != TELEGRAM_BOT_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return True


def process_response(response: TelegramMethod) -> dict[str, Any]:
    if not response:
        return {}

    if hasattr(response, "name") and response.name == "UNHANDLED":
        return {}

    result = {"method": response.__api_method__}
    for key, value in response.model_dump(warnings=False, exclude_none=True).items():
        prepared_value = prepare_value(value=value, bot=bot, files={})

        if prepared_value:
            result[key] = prepared_value

    return result


@router.post(path="/telegram", response_class=ORJSONResponse)
async def webhook(_: Annotated[bool, Depends(auth_telegram)], body: Any = Body()) -> ORJSONResponse:
    _response = await root_dispatcher.feed_raw_update(update=body, bot=bot)

    response = process_response(response=_response)
    struct_log(event="Response", data=response)

    return ORJSONResponse(
        content=response,
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    await init_db()
    await bot.setup()
    yield


def get_app() -> FastAPI:
    fastapi = FastAPI(lifespan=lifespan)
    fastapi.include_router(router)
    fastapi.include_router(endpoints.router)
    return fastapi
