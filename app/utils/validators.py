from fastapi import HTTPException
from typing import List

class FileValidator:
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg',
        'image/png',
        'text/plain',
        'application/json',
        'application/xml'
    ]
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def validate_file(cls, file_size: int, mime_type: str):
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file not allowed"
            )
            
        if file_size > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {cls.MAX_FILE_SIZE/1024/1024}MB"
            )
            
        if mime_type not in cls.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            ) 