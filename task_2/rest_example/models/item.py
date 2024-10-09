from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    name: str
    price: float = Field(..., gt=0.0, description="Цена товара")
    deleted: bool = Field(default=False, description="Статус удаления товара")


class ItemCreateRequest(ItemBase):
    """Модель для создания нового товара."""

    pass


class ItemUpdateRequest(BaseModel):
    """Модель для частичного обновления товара (нельзя менять deleted)."""

    name: Optional[str] = None
    price: Optional[float] = Field(None, gt=0.0, description="Цена товара")

    model_config = ConfigDict(extra="forbid")


class ItemResponse(ItemBase):
    """Ответ с информацией о товаре."""

    id: int = Field(..., description="Идентификатор товара")
