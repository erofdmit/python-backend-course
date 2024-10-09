from pydantic import BaseModel
from uuid import UUID
from typing import List


class CreateChatResponse(BaseModel):
    chat_id: UUID


class PublishMessageRequest(BaseModel):
    message: str


class ChatListResponse(BaseModel):
    chat_ids: List[UUID]
