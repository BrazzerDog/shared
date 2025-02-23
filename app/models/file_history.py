from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FileHistoryModel(Base):
    __tablename__ = "file_history"
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    action = Column(String)  # CREATED, UPDATED, DELETED
    service = Column(String, nullable=False)  # Кто изменил
    created_at = Column(DateTime, default=datetime.utcnow) 