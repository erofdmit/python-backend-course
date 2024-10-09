# models/cart.py
from typing import List
from pydantic import BaseModel, Field, model_validator
from .item import ItemResponse


class CartItem(BaseModel):
    item: ItemResponse  # Включаем всю информацию о товаре
    quantity: int = Field(ge=0, description="Количество товара в корзине")
    available: bool = Field(default=True, description="Доступен ли товар")


class CartBase(BaseModel):
    items: List[CartItem] = Field(default=[], description="Список товаров в корзине")
    price: float = Field(default=0.0, ge=0.0, description="Общая сумма заказа")

    @model_validator(mode="before")
    def recalculate_price(cls, values):
        """Автоматический пересчет стоимости корзины перед валидацией."""
        items = values.get("items", [])
        total_price = sum(
            item.item.price * item.quantity
            for item in items
            if not item.item.deleted and item.available
        )
        values["price"] = total_price
        return values

    @model_validator(mode="before")
    def validate_items(cls, values):
        """Удаляет товары, которые помечены как удаленные, из списка корзины перед валидацией."""
        items = values.get("items", [])
        filtered_items = [item for item in items if not item.item.deleted]
        if len(filtered_items) != len(items):
            values["items"] = filtered_items
        return values


class CartCreateRequest(BaseModel):
    """Запрос на создание пустой корзины (без тела)."""

    pass


class CartResponse(CartBase):
    id: int = Field(..., description="Идентификатор корзины")
