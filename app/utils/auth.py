from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

class AuthService:
    def __init__(self):
        # Для первоначального запуска
        self.api_keys = {
            "admin_key": "ADMIN"  # Временный ключ для создания первого админа
        }
    
    async def authenticate(
        self,
        api_key: str = Depends(API_KEY_HEADER),
        db: AsyncSession = Depends(get_db)
    ) -> str:
        # Проверяем временный ключ админа
        if api_key in self.api_keys:
            return self.api_keys[api_key]
            
        # Проверяем токен в БД
        query = select(UserModel).where(UserModel.token == api_key)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
            
        return user.service

    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> UserModel:
        query = select(UserModel).where(
            UserModel.token == token,
            UserModel.is_active == True
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        return user 