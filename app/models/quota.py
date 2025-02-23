from sqlalchemy import Column, Integer, String, BigInteger
from app.database import Base

class QuotaModel(Base):
    __tablename__ = "quotas"
    
    id = Column(Integer, primary_key=True)
    service_id = Column(String, nullable=False, unique=True)
    max_bytes = Column(BigInteger, nullable=False)  # Максимальный размер в байтах
    used_bytes = Column(BigInteger, default=0)      # Использовано байт 