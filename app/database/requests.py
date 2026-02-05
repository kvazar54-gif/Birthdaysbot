from app.database.models import async_session
from app.database.models import User, Celebrant
from sqlalchemy import select, update, delete
import aiosqlite


DB_NAME = 'db.sqlite3'

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def adding_celebrant(tg_id, name, event_date):
    async with async_session() as session:
        new_celebrant = Celebrant(tg_id=tg_id, name=name, event_date=event_date)
        session.add(new_celebrant)
        await session.commit()


async def get_celebrants(tg_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, event_date FROM celebrants WHERE tg_id=?", 
            (tg_id,)
        ) as cursor:
            return await cursor.fetchall()


async def delete_celebrant(tg_id, name):
    """ИСПРАВЛЕНО: Добавлен параметр tg_id для безопасного удаления"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM celebrants WHERE tg_id = ? AND name = ?", 
            (tg_id, name)
        )
        await db.commit()
