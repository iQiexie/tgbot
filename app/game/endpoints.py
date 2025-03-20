from typing import Annotated

from aiogram.types import LabeledPrice
from fastapi import APIRouter, Depends
from fastapi.security import APIKeyHeader

from app.game.dto import InvoiceData
from app.patches import WebappData, bot

router = APIRouter(tags=["Game endpoints"], prefix="/api/v1")
AuthUserHeader = APIKeyHeader(name="token", scheme_name="AuthUser", auto_error=True)


async def get_current_user(webapp_data: str = Depends(AuthUserHeader)) -> WebappData:
    return bot.auth_webapp(webapp_data=webapp_data)


@router.post(path="/invoice")
async def get_invoice_url(
    current_user: Annotated[WebappData, Depends(get_current_user)],
    data: InvoiceData,
) -> dict[str, str]:
    resp = await bot.create_invoice_link(
        title=data.title,
        description=data.description,
        payload=str(current_user.telegram_id),
        currency="XTR",
        prices=[LabeledPrice(label=data.price_label, amount=data.price_amount)],
    )

    return {"data": resp}
