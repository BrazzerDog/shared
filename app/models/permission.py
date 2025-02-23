from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class PermissionModel(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    service_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    permission = Column(String, nullable=False)
    target_service = Column(String, nullable=False)

    class Config:
        orm_mode = True 