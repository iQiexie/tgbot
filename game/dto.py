from pydantic import BaseModel, Field


class InvoiceData(BaseModel):
    title: str
    description: str | None = Field(default="Покупка за Telegram Stars")
    price_label: str | None = Field(default="Покупка за Telegram Stars")
    price_amount: int
