from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.file_service import FileService
from app.utils.auth import AuthService
from app.database import get_db

router = APIRouter()
auth_service = AuthService()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    service: str = Depends(auth_service.authenticate),
    db: AsyncSession = Depends(get_db)
):
    file_service = FileService("./storage", db)
    return await file_service.save_file(file, service)

@router.get("/list")
async def list_files(
    service: str = Depends(auth_service.authenticate),
    db: AsyncSession = Depends(get_db)
):
    file_service = FileService("./storage", db)
    return await file_service.get_available_files(service) 