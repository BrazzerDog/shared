from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    service = Column(String, nullable=False)  # 1C/BITRIX/PORTAL
    role = Column(String, nullable=False)     # admin/user
    token = Column(String, unique=True)       # API токен
    is_active = Column(Boolean, default=True) 