import aiosqlite
from typing import Optional
from config import DB_PATH
from patches import WebappData


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Create users table if it doesn't exist
        await db.execute('''
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
        ''')
        await db.commit()


async def insert_webapp_data(data: WebappData) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        # Convert is_premium to integer for SQLite (which doesn't have a native boolean type)
        is_premium_int = 1 if data.is_premium else 0 if data.is_premium is not None else None

        # Insert or replace user data
        await db.execute('''
        INSERT OR REPLACE INTO users 
        (telegram_id, language_code, username, first_name, last_name, is_premium, photo_url, start_param)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.telegram_id,
            data.language_code,
            data.username,
            data.first_name,
            data.last_name,
            is_premium_int,
            data.photo_url,
            data.start_param
        ))
        await db.commit()
        return True


async def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    stmt = "SELECT * FROM users WHERE telegram_id = ?"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(stmt, (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
