from typing import List, Optional
from app.models.permission import PermissionModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import UserModel
from app.models.file import FileModel

class PermissionService:
    PERMISSIONS = {
        "admin": [
            "CREATE_USER",    # Создание пользователей
            "DELETE_USER",    # Удаление пользователей
            "VIEW_ALL",       # Просмотр всех файлов
            "EDIT_ALL",       # Редактирование всех файлов
            "DELETE_ALL"      # Удаление всех файлов
        ],
        "user": {
            "1C": ["VIEW_ALL", "EDIT_ALL", "DELETE_ALL"],
            "BITRIX": ["VIEW_ALL", "EDIT_ALL", "DELETE_ALL"],
            "PORTAL": ["VIEW_ALL", "EDIT_ALL", "DELETE_ALL"]
        }
    }

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def check_permission(self, service: str, permission: str) -> bool:
        # В MVP все сервисы имеют полный доступ к файлам
        if service in ["1C_SERVICE", "BITRIX_SERVICE", "PORTAL_SERVICE"]:
            return True
        elif service == "ADMIN":
            return True
        return False

    async def add_permission(self, permission_data: dict) -> PermissionModel:
        permission = PermissionModel(**permission_data)
        self.db.add(permission)
        await self.db.commit()
        return permission

    async def init_default_permissions(self):
        default_permissions = [
            # 1C права
            {"service_id": "1C_SERVICE", "role": "1C_SERVICE", "permission": "READ_OWN", "target_service": "1C_SERVICE"},
            {"service_id": "1C_SERVICE", "role": "1C_SERVICE", "permission": "WRITE_OWN", "target_service": "1C_SERVICE"},
            {"service_id": "1C_SERVICE", "role": "1C_SERVICE", "permission": "READ_SHARED", "target_service": "BITRIX_SERVICE"},
            
            # Битрикс права
            {"service_id": "BITRIX_SERVICE", "role": "BITRIX_SERVICE", "permission": "READ_OWN", "target_service": "BITRIX_SERVICE"},
            {"service_id": "BITRIX_SERVICE", "role": "BITRIX_SERVICE", "permission": "WRITE_OWN", "target_service": "BITRIX_SERVICE"},
            {"service_id": "BITRIX_SERVICE", "role": "BITRIX_SERVICE", "permission": "READ_SHARED", "target_service": "1C_SERVICE"},
            
            # Портал права
            {"service_id": "PORTAL_SERVICE", "role": "PORTAL_SERVICE", "permission": "READ_OWN", "target_service": "PORTAL_SERVICE"},
            {"service_id": "PORTAL_SERVICE", "role": "PORTAL_SERVICE", "permission": "WRITE_OWN", "target_service": "PORTAL_SERVICE"},
            
            # Админ права
            {"service_id": "ADMIN", "role": "ADMIN", "permission": "MANAGE_ALL", "target_service": "*"}
        ]
        
        for perm in default_permissions:
            await self.add_permission(perm)

    async def can_edit(self, user: UserModel, file: FileModel) -> bool:
        """
        Проверяет права пользователя на редактирование файла
        """
        # Админ своего сервиса может редактировать файлы сервиса
        if user.role == "admin" and user.service == file.owner_service:
            return True
        
        # Пользователь может редактировать только свои файлы
        if user.service == file.owner_service:
            return True
        
        return False 