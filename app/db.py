from typing import Optional

import aiosqlite

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
