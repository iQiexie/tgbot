from typing import Optional

import aiosqlite
from aiogram.types import SuccessfulPayment

from app.patches import WebappData
from config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            language_code TEXT,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_premium BOOLEAN,
            photo_url TEXT,
            start_param TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            currency TEXT,
            total_amount INTEGER,
            invoice_payload TEXT,
            telegram_payment_charge_id TEXT,
            provider_payment_charge_id TEXT,
            subscription_expiration_date INTEGER,
            is_recurring BOOLEAN,
            is_first_recurring BOOLEAN,
            shipping_option_id TEXT,
            order_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )
        """
        )

        columns = await db.execute("PRAGMA table_info(transactions)")
        columns = [row[1] for row in await columns.fetchall()]

        if 'unique_id' not in columns:
            await db.execute("ALTER TABLE transactions ADD COLUMN unique_id TEXT")

        await db.commit()


async def insert_webapp_data(data: WebappData) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        # Convert is_premium to integer for SQLite (which doesn't have a native boolean type)
        is_premium_int = 1 if data.is_premium else 0 if data.is_premium is not None else None

        # Insert or replace user data using named parameters
        await db.execute(
            """
        INSERT OR REPLACE INTO users
        (telegram_id, language_code, username, first_name, last_name, is_premium, photo_url, start_param)
        VALUES (:telegram_id, :language_code, :username, :first_name, :last_name, :is_premium,
        :photo_url, :start_param)
        """,
            {
                "telegram_id": data.telegram_id,
                "language_code": data.language_code,
                "username": data.username,
                "first_name": data.first_name,
                "last_name": data.last_name,
                "is_premium": is_premium_int,
                "photo_url": data.photo_url,
                "start_param": data.start_param,
            },
        )
        await db.commit()
        return True


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    stmt = "SELECT * FROM users WHERE telegram_id = :telegram_id"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(stmt, {"telegram_id": telegram_id}) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def insert_transaction(payment: SuccessfulPayment, user_id: int, unique_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        # Convert boolean values to integers for SQLite
        is_recurring_int = 1 if payment.is_recurring else 0 if payment.is_recurring is not None else None
        is_first_recurring_int = 1 if payment.is_first_recurring else 0 if payment.is_first_recurring is not None else None

        await db.execute(
            """
        INSERT INTO transactions
        (telegram_id, currency, total_amount, invoice_payload, telegram_payment_charge_id,
        provider_payment_charge_id, subscription_expiration_date, is_recurring, is_first_recurring,
        shipping_option_id, order_info, unique_id)
        VALUES (:telegram_id, :currency, :total_amount, :invoice_payload, :telegram_payment_charge_id,
        :provider_payment_charge_id, :subscription_expiration_date, :is_recurring, :is_first_recurring,
        :shipping_option_id, :order_info, :unique_id)
        """,
            {
                "telegram_id": user_id,
                "currency": payment.currency,
                "total_amount": payment.total_amount,
                "invoice_payload": payment.invoice_payload,
                "telegram_payment_charge_id": payment.telegram_payment_charge_id,
                "provider_payment_charge_id": payment.provider_payment_charge_id,
                "subscription_expiration_date": payment.subscription_expiration_date,
                "is_recurring": is_recurring_int,
                "is_first_recurring": is_first_recurring_int,
                "shipping_option_id": payment.shipping_option_id,
                "order_info": payment.order_info,
                "unique_id": unique_id,
            },
        )
        await db.commit()
        return True


async def check_invoice_paid(unique_id: str) -> bool:
    stmt = """select telegram_id from transactions where unique_id = :unique_id"""

    async with aiosqlite.connect(DB_PATH) as db:
        resp = await db.execute(stmt, {"unique_id": unique_id})
        resp = await resp.fetchone()
        paid = bool(resp)

    return paid
