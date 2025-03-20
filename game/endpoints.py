from typing import Annotated

from aiogram.types import LabeledPrice
from fastapi import APIRouter
from fastapi import Depends
from fastapi.security import APIKeyHeader

from game.dto import InvoiceData
from patches import WebappData
from patches import bot

router = APIRouter(tags=["Game endpoints"], prefix="/api/v1")
AuthUserHeader = APIKeyHeader(name="token", scheme_name="AuthUser", auto_error=True)


async def get_current_user(webapp_data: str = Depends(AuthUserHeader)) -> WebappData:
    return bot.auth_webapp(webapp_data=webapp_data)


@router.post(path="/invoice")
async def get_invoice_url(
    current_user: Annotated[WebappData, Depends(get_current_user)],
    data: InvoiceData,
) -> str:
    return await bot.create_invoice_link(
        title=data.title,
        description=data.description,
        payload=str(current_user.telegram_id),
        currency="XTR",
        prices=[LabeledPrice(label=data.price_label, amount=data.price_amount)],
    )
