from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.utils.auth import AuthService
from app.services.file_service import FileService
from app.models.file import FileModel
from datetime import datetime
import secrets
import uuid
from app.models.user import UserModel
from app.models.permission import PermissionModel

router = APIRouter()
auth_service = AuthService()

@router.delete("/cleanup")
async def cleanup_expired_files(
    service: str = Depends(auth_service.authenticate),
    db: AsyncSession = Depends(get_db)
):
    if service != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can cleanup files")
        
    file_service = FileService("/storage", db)
    query = select(FileModel).where(
        FileModel.expires_at < datetime.now()
    )
    result = await db.execute(query)
    expired_files = result.scalars().all()
    
    for file in expired_files:
        await file_service.delete_file(file.id, "ADMIN")
        
    return {"deleted_files": len(expired_files)}

@router.post("/users/create")
async def create_service_user(
    service: str = Depends(auth_service.authenticate),
    service_type: str = Query(..., enum=["1C", "BITRIX", "PORTAL"]),
    db: AsyncSession = Depends(get_db)
):
    if service != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can create users")

    # Генерируем простой токен для MVP
    token = secrets.token_urlsafe(32)
    
    user = UserModel(
        username=f"{service_type}_USER",
        service=service_type,
        role="user",
        token=token,
        is_active=True
    )
    
    try:
        db.add(user)
        await db.commit()
        
        return {
            "username": user.username,
            "service": user.service,
            "token": token
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 