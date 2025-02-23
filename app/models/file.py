from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime

class FileModel(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    hash = Column(String, nullable=False)  # Для проверки версии
    owner_service = Column(String, nullable=False)  # 1C/BITRIX/PORTAL
    version = Column(Integer, default=1)  # Добавляем версию
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    service = Column(String, nullable=False)
    is_shared = Column(Boolean, default=False)
    mime_type = Column(String)
    expires_at = Column(DateTime, nullable=True)
    is_locked = Column(Boolean, default=False)  # Флаг блокировки
    locked_by = Column(String, nullable=True)   # Кто заблокировал
    locked_at = Column(DateTime, nullable=True)  # Когда заблокировал 