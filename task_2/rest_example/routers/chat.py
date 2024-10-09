from dataclasses import dataclass, field
from uuid import uuid4, UUID
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Request
from fastapi.responses import JSONResponse

from ..models.chat import ChatListResponse, CreateChatResponse, PublishMessageRequest

router = APIRouter(prefix='/chat')

class Broadcaster:
    def __init__(self):
        self.subscribers: List[WebSocket] = []

    async def subscribe(self, ws: WebSocket):
        await ws.accept()
        self.subscribers.append(ws)

    async def unsubscribe(self, ws: WebSocket):
        if ws in self.subscribers:
            self.subscribers.remove(ws)

    async def publish(self, message: str):
        disconnected = []
        for ws in self.subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            await self.unsubscribe(ws)


# In-memory хранилище для чатов
chat_rooms: Dict[UUID, Broadcaster] = {}


@router.post("/", response_model=CreateChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat():
    chat_id = uuid4()
    chat_rooms[chat_id] = Broadcaster()
    return CreateChatResponse(chat_id=chat_id)


@router.get("/", response_model=ChatListResponse)
async def list_chats():
    return ChatListResponse(chat_ids=list(chat_rooms.keys()))


@router.post("/publish/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def publish_message(chat_id: UUID, payload: PublishMessageRequest):
    broadcaster = chat_rooms.get(chat_id)
    if not broadcaster:
        raise HTTPException(status_code=404, detail="Chat ID not found")
    await broadcaster.publish(payload.message)
    return {"detail": "Message published"}


@router.websocket("/subscribe/{chat_id}")
async def subscribe_chat(websocket: WebSocket, chat_id: UUID):
    if chat_id not in chat_rooms:
        await websocket.close(code=1008)
        return

    broadcaster = chat_rooms[chat_id]
    client_id = uuid4()
    await broadcaster.subscribe(websocket)
    await broadcaster.publish(f"Клиент {client_id} подключился к чату {chat_id}")

    try:
        while True:
            data = await websocket.receive_text()
            await broadcaster.publish(f"Клиент {client_id}: {data}")
    except WebSocketDisconnect:
        await broadcaster.unsubscribe(websocket)
        await broadcaster.publish(f"Клиент {client_id} отключился от чата {chat_id}")