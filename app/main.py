from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select, text, ForeignKey
import os
import aiofiles
import secrets
from datetime import datetime
from transliterate import translit
import re
from fastapi.responses import FileResponse

# База данных
DATABASE_URL = "sqlite+aiosqlite:///./storage.db"
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Модели
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    service = Column(String, nullable=False)  # 1C/BITRIX/PORTAL
    role = Column(String, nullable=False)     # admin/user
    token = Column(String, unique=True)
    is_active = Column(Boolean, default=True)

class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    owner_service = Column(String, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuotaModel(Base):
    __tablename__ = "quotas"
    id = Column(Integer, primary_key=True)
    service_id = Column(String, nullable=False)
    max_bytes = Column(Integer, nullable=False)
    used_bytes = Column(Integer, nullable=False)

class FileHistoryModel(Base):
    __tablename__ = "file_history"
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    action = Column(String)  # CREATED, UPDATED, DELETED
    service = Column(String, nullable=False)  # Кто изменил
    created_at = Column(DateTime, default=datetime.utcnow)

# Приложение
app = FastAPI(title="File Storage MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Аутентификация
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

async def authenticate(
    api_key: str = Depends(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db)
) -> str:
    # Проверяем токен админа
    if api_key == "admin_token":
        return "ADMIN"
        
    # Проверка токена в БД
    result = await db.execute(
        select(UserModel).where(
            UserModel.token == api_key,
            UserModel.is_active == True
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Выводим все токены для отладки
        all_tokens = await db.execute(select(UserModel.token))
        tokens = [t[0] for t in all_tokens]
        print(f"Доступные токены в БД: {tokens}")
        print(f"Переданный токен: {api_key}")
        
        raise HTTPException(
            status_code=401,
            detail="Неверный токен. Используйте admin_token или токен сервиса"
        )
        
    return user.service

# Инициализация
@app.on_event("startup")
async def startup():
    # Создаем директории
    os.makedirs("./storage", exist_ok=True)
    for service in ["1C", "BITRIX", "PORTAL", "ADMIN"]:
        os.makedirs(f"./storage/{service}", exist_ok=True)
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем админа с фиксированным токеном
    async with async_session() as db:
        admin = UserModel(
            username="admin",
            service="ADMIN",
            role="admin",
            token="admin_token", # Фиксированный токен для простоты
            is_active=True
        )
        try:
            db.add(admin)
            await db.commit()
            print("\nИспользуйте admin_token для авторизации админа\n")
        except:
            print("\nАдмин уже существует, используйте admin_token\n")

# API эндпоинты
@app.post("/api/admin/users/create")
async def create_user(
    service_type: str,
    current_service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    """Создание пользователя сервиса"""
    
    if current_service != "ADMIN":
        raise HTTPException(
            status_code=403, 
            detail="Нужен токен админа (admin_token)"
        )
    
    service_type = service_type.upper()
    if service_type not in ["1C", "BITRIX", "PORTAL"]:
        raise HTTPException(
            status_code=400, 
            detail="service_type должен быть: BITRIX, 1C или PORTAL"
        )
    
    token = f"{service_type.lower()}_token"
    
    # Проверяем существование
    result = await db.execute(
        select(UserModel).where(UserModel.service == service_type)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Обновляем токен существующего пользователя
        existing_user.token = token
        await db.commit()
        return {
            "service": service_type,
            "token": token,
            "message": f"Токен обновлен. Используйте: {token}"
        }
    
    # Создаем нового пользователя
    user = UserModel(
        username=f"{service_type}_USER",
        service=service_type,
        role="user",
        token=token,
        is_active=True
    )
    
    db.add(user)
    await db.commit()
    
    print(f"Создан пользователь: {service_type}, токен: {token}")
    
    return {
        "service": service_type,
        "token": token,
        "message": f"Пользователь создан. Используйте токен: {token}"
    }

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Сохраняем файл
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = f"./storage/{service}/{filename}"
        
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Создаем запись в БД
        db_file = FileModel(
            filename=file.filename,
            path=file_path,
            owner_service=service
        )
        db.add(db_file)
        await db.commit()
        
        # Логируем создание
        history = FileHistoryModel(
            file_id=db_file.id,
            action="CREATED",
            service=service
        )
        db.add(history)
        await db.commit()
        
        return {
            "id": db_file.id,
            "filename": db_file.filename,
            "owner": db_file.owner_service,
            "action": "CREATED"
        }
        
    except Exception as e:
        print(f"Ошибка при загрузке файла: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки файла: {str(e)}"
        )

@app.get("/api/files/list")
async def list_files(
    service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FileModel))
    files = result.scalars().all()
    
    return [{
        "id": f.id,
        "filename": f.filename,
        "owner": f.owner_service,
        "created_at": f.created_at
    } for f in files]

@app.get("/api/files/changes")
async def get_changes(
    since: datetime,
    service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка изменений с определенного момента"""
    
    query = select(FileHistoryModel).where(
        FileHistoryModel.created_at > since
    ).order_by(FileHistoryModel.created_at)
    
    result = await db.execute(query)
    changes = result.scalars().all()
    
    return [{
        "file_id": c.file_id,
        "action": c.action,
        "service": c.service,
        "timestamp": c.created_at
    } for c in changes]

@app.get("/api/files/{file_id}/download")
async def download_file(
    file_id: int,
    service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FileModel).where(FileModel.id == file_id)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден")
        
    return FileResponse(
        file.path,
        filename=file.filename,
        media_type='application/octet-stream'
    )

@app.get("/api/files/{filename}/version")
async def get_file_version(
    filename: str,
    service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FileModel).where(FileModel.filename == filename)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден")
        
    return {
        "filename": file.filename,
        "version": file.version,
        "last_modified": file.created_at
    }

@app.post("/api/files/{filename}/update")
async def update_file(
    filename: str,
    file: UploadFile = File(...),
    service: str = Depends(authenticate),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем существующий файл
    result = await db.execute(
        select(FileModel).where(FileModel.filename == filename)
    )
    existing_file = result.scalar_one_or_none()
    
    if not existing_file:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Сохраняем новую версию
    new_path = f"./storage/{service}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    content = await file.read()
    async with aiofiles.open(new_path, 'wb') as f:
        await f.write(content)
    
    # Обновляем запись в БД
    existing_file.path = new_path
    existing_file.version += 1
    existing_file.created_at = datetime.utcnow()
    
    # Логируем изменение
    history = FileHistoryModel(
        file_id=existing_file.id,
        action="UPDATED",
        service=service
    )
    db.add(history)
    await db.commit()
    
    return {
        "filename": filename,
        "version": existing_file.version,
        "action": "UPDATED"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 