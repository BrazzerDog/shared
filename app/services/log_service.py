from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.log import AccessLogModel

class LogService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log_action(
        self,
        file_id: int,
        service_id: str,
        action: str,
        request: Request,
        status: str = "success",
        error_detail: str = None
    ):
        try:
            log = AccessLogModel(
                file_id=file_id,
                service_id=service_id,
                action=action,
                ip_address=request.client.host,
                status=status,
                error_detail=error_detail
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            print(f"Error logging action: {e}")
            # Не поднимаем исключение, чтобы не блокировать основной функционал 