import asyncio
from app.database import init_db, async_session
from app.models.user import UserModel
import secrets

async def create_admin():
    async with async_session() as db:
        # Проверяем существование админа
        admin = await db.get(UserModel, 1)
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
            print(f"Admin created with token: {token}")
        else:
            print("Admin already exists")

if __name__ == "__main__":
    asyncio.run(create_admin()) 