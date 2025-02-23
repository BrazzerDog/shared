from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.database import get_db
from app.models.file import FileModel
from app.models.log import AccessLogModel
from app.utils.auth import AuthService
from datetime import datetime, timedelta

router = APIRouter()
auth_service = AuthService()

@router.get("")
async def get_stats(
    service: str = Depends(auth_service.authenticate),
    db: AsyncSession = Depends(get_db)
):
    if service != "ADMIN":
        raise HTTPException(status_code=403, detail="Only admin can view stats")
        
    # Статистика по файлам
    files_query = select(
        func.count(FileModel.id),
        func.sum(FileModel.size),
        func.count(FileModel.id).filter(FileModel.is_shared == True)
    )
    files_result = await db.execute(files_query)
    total_files, total_size, shared_files = files_result.first()

    # Статистика по действиям
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    logs_query = select(
        AccessLogModel.action,
        func.count(AccessLogModel.id)
    ).filter(
        AccessLogModel.timestamp > week_ago
    ).group_by(
        AccessLogModel.action
    )
    logs_result = await db.execute(logs_query)
    actions_stats = dict(logs_result.all())

    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "shared_files": shared_files,
        "weekly_actions": actions_stats
    } 