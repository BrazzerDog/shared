from fastapi import UploadFile, HTTPException
import aiofiles
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import FileModel
from app.services.permission_service import PermissionService
from app.utils.validators import FileValidator
from app.services.quota_service import QuotaService
from werkzeug.utils import secure_filename

class FileService:
    def __init__(self, storage_path: str, db_session: AsyncSession):
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
        self.storage_path = storage_path
        self.db = db_session
        self.permission_service = PermissionService(db_session)
        self.quota_service = QuotaService(db_session)

    async def save_file(self, file: UploadFile, service: str) -> FileModel:
        try:
            content = await file.read()
            file_size = len(content)
            
            # Базовая валидация
            FileValidator.validate_file(file_size, file.content_type)
            
            # Создаем директорию если нужно
            service_path = os.path.join(self.storage_path, service)
            os.makedirs(service_path, exist_ok=True)
            
            # Сохраняем файл
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            file_path = os.path.join(service_path, filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            file_model = FileModel(
                filename=file.filename,
                path=file_path,
                size=file_size,
                hash=hashlib.md5(content).hexdigest(),
                owner_service=service
            )
            
            self.db.add(file_model)
            await self.db.commit()
            return file_model
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def _save_file_to_storage(self, file: UploadFile, content: bytes, service: str) -> dict:
        try:
            service_path = os.path.join(self.storage_path, service)
            
            # Проверяем и создаем директорию
            if not os.path.exists(self.storage_path):
                raise HTTPException(
                    status_code=500,
                    detail="Storage root directory does not exist"
                )
            
            os.makedirs(service_path, exist_ok=True)
            
            # Проверяем права на запись
            if not os.access(service_path, os.W_OK):
                raise HTTPException(
                    status_code=500,
                    detail="No write permission to storage directory"
                )
            
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = secure_filename(file.filename)  # Добавляем безопасное имя файла
            filename = f"{timestamp}_{safe_filename}"
            file_path = os.path.join(service_path, filename)
            
            # Сохраняем файл
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            return {
                "path": file_path,
                "hash": hashlib.md5(content).hexdigest()
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file: {str(e)}"
            )

    async def get_file(self, file_id: int, service: str):
        query = select(FileModel).where(FileModel.id == file_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def validate_access(self, file_id: int, service: str, permission: str) -> bool:
        # Для MVP - всегда разрешаем доступ сервисам
        if service in ["1C_SERVICE", "BITRIX_SERVICE", "PORTAL_SERVICE"]:
            return True
        return False

    async def list_files(self, service: str, search: str = None) -> List[FileModel]:
        query = select(FileModel)
        
        # Фильтруем по владельцу или shared файлам
        query = query.where(
            (FileModel.owner_service == service) |
            (FileModel.is_shared == True)
        )
        
        if search:
            query = query.where(FileModel.filename.contains(search))
            
        result = await self.db.execute(query)
        return result.scalars().all()

    async def share_file(self, file_id: int, service: str) -> FileModel:
        file = await self.get_file(file_id, service)
        
        if file.owner_service != service:
            raise HTTPException(status_code=403, detail="Can only share own files")
            
        file.is_shared = True
        await self.db.commit()
        return file

    async def extend_file(self, file_id: int, service: str, days: int = 30) -> FileModel:
        file = await self.get_file(file_id, service)
        
        if file.owner_service != service and service != "ADMIN":
            raise HTTPException(status_code=403, detail="Can only extend own files")
        
        if days <= 0:
            raise HTTPException(status_code=400, detail="Days must be positive")
        
        if days > 365:
            raise HTTPException(status_code=400, detail="Maximum extension is 365 days")
        
        file.expires_at = datetime.now() + timedelta(days=days)
        await self.db.commit()
        return file

    async def delete_file(self, file_id: int, service: str):
        file = await self.get_file(file_id, service)
        
        if file.owner_service != service and service != "ADMIN":
            raise HTTPException(status_code=403, detail="Can only delete own files")
            
        # Обновляем квоту перед удалением
        await self.quota_service.update_quota(file.owner_service, file.size, increment=False)
            
        # Удаляем физический файл
        try:
            os.remove(file.path)
        except OSError as e:
            # Логируем ошибку, но продолжаем удаление из БД
            print(f"Error deleting file {file.path}: {e}")
            
        await self.db.delete(file)
        await self.db.commit()

    async def get_available_files(self, service: str) -> List[FileModel]:
        query = select(FileModel)
        result = await self.db.execute(query)
        return result.scalars().all() 