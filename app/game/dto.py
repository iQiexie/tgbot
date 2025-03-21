from pydantic import BaseModel, Field


class InvoiceRequest(BaseModel):
    title: str
    description: str | None = Field(default="Покупка за Telegram Stars")
    price_label: str | None = Field(default="Покупка за Telegram Stars")
    price_amount: int


class InvoiceResponse(BaseModel):
    data: str
    id: str


class InvoiceStatusResponse(BaseModel):
    paid: bool
