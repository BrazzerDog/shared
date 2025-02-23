from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime

class AccessLogModel(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    service_id = Column(String)
    action = Column(String)
    timestamp = Column(DateTime)
    file_hash = Column(String)
    ip_address = Column(String)
    status = Column(String) 