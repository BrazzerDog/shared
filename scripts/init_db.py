import asyncio
from app.database import init_db
from app.models.user import UserModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
import secrets

async def init():
    # Создаем таблицы
    await init_db()
    
    # Создаем админа
    async with async_session() as db:
        # Проверяем существование админа
        query = select(UserModel).where(UserModel.role == "admin")
        result = await db.execute(query)
        admin = result.scalar_one_or_none()
        
        if not admin:
            token = secrets.token_urlsafe(32)
            admin = UserModel(
                username="admin",
                service="ADMIN",
                role="admin",
                token=token,
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print(f"Admin token: {token}")
        else:
            print("Admin already exists")

if __name__ == "__main__":
    asyncio.run(init()) 