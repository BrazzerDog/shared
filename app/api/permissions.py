from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.permission import PermissionModel
from app.utils.auth import AuthService
from typing import List
from sqlalchemy import select

router = APIRouter()
auth_service = AuthService()

@router.get("/{service_id}")
async def get_service_permissions(
    service_id: str,
    current_service: str = Depends(auth_service.authenticate),
    db: AsyncSession = Depends(get_db)
):
    # Только админ или сам сервис может смотреть свои права
    if current_service != "ADMIN" and current_service != service_id:
        raise HTTPException(status_code=403, detail="Not authorized to view permissions")
        
    query = select(PermissionModel).where(PermissionModel.service_id == service_id)
    result = await db.execute(query)
    permissions = result.scalars().all()
    
    return permissions 