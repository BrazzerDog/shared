from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.quota import QuotaModel
from fastapi import HTTPException

class QuotaService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
    async def init_default_quotas(self):
        default_quotas = [
            {"service_id": "1C_SERVICE", "max_bytes": 10 * 1024 * 1024 * 1024},  # 10GB
            {"service_id": "BITRIX_SERVICE", "max_bytes": 10 * 1024 * 1024 * 1024},
            {"service_id": "PORTAL_SERVICE", "max_bytes": 5 * 1024 * 1024 * 1024},  # 5GB
        ]
        
        for quota_data in default_quotas:
            # Проверяем существование квоты перед добавлением
            query = select(QuotaModel).where(
                QuotaModel.service_id == quota_data["service_id"]
            )
            result = await self.db.execute(query)
            existing_quota = result.scalar_one_or_none()
            
            if not existing_quota:
                quota = QuotaModel(**quota_data)
                self.db.add(quota)
                try:
                    await self.db.commit()
                except Exception as e:
                    print(f"Error adding quota for {quota_data['service_id']}: {e}")
                    await self.db.rollback()
            
    async def add_quota(self, quota_data: dict):
        try:
            query = select(QuotaModel).where(
                QuotaModel.service_id == quota_data["service_id"]
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Quota for service {quota_data['service_id']} already exists"
                )
            
            quota = QuotaModel(**quota_data)
            self.db.add(quota)
            await self.db.commit()
            return quota
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Error adding quota: {str(e)}"
            )
        
    async def check_quota(self, service_id: str, file_size: int):
        query = select(QuotaModel).where(QuotaModel.service_id == service_id)
        result = await self.db.execute(query)
        quota = result.scalar_one_or_none()
        
        if not quota:
            return True  # Если квота не установлена, разрешаем
            
        if quota.used_bytes + file_size > quota.max_bytes:
            raise HTTPException(
                status_code=400,
                detail="Storage quota exceeded"
            )
            
    async def update_quota(self, service_id: str, file_size: int, increment: bool = True):
        if file_size < 0:
            raise HTTPException(
                status_code=400,
                detail="File size cannot be negative"
            )
        
        query = select(QuotaModel).where(QuotaModel.service_id == service_id)
        result = await self.db.execute(query)
        quota = result.scalar_one_or_none()
        
        if quota:
            try:
                if increment:
                    quota.used_bytes += file_size
                else:
                    quota.used_bytes = max(0, quota.used_bytes - file_size)
                await self.db.commit()
            except Exception as e:
                await self.db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating quota: {str(e)}"
                ) 