from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index_page(
    request: Request,
    user: UserModel = Depends(get_current_user)
):
    """
    Главная страница с файлами всех систем согласно правам пользователя
    """
    # Получаем файлы из всех систем к которым есть доступ
    files = await file_service.get_available_files(user.service)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "files": files,
        "services": ["1C", "BITRIX", "PORTAL"]
    })

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Получаем токен из query параметров
        token = websocket.query_params.get("token")
        user = await auth_service.get_user_by_token(token)
        if not user:
            await websocket.close(code=4001)
            return
            
        while True:
            files = await file_service.get_available_files(user.service)
            await websocket.send_json({"files": files})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass 