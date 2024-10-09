from fastapi import APIRouter, HTTPException, Depends, Response, Query, Body
from typing import List, Optional
from aiosqlite import Connection
from http import HTTPStatus
from ..models.item import ItemResponse, ItemCreateRequest, ItemUpdateRequest
from ..db.db_engine import get_db_connection
from ..db.crud import create_item, get_item, get_items_list, update_item, delete_item
from ..errors import ItemNotFoundException, ItemNotModifiedException

router = APIRouter(prefix='/item')

@router.post("/", response_model=ItemResponse, status_code=HTTPStatus.CREATED)
async def create_new_item(item: ItemCreateRequest, response: Response, conn: Connection = Depends(get_db_connection)):
    """Создание нового товара."""
    created_item = await create_item(conn, item)
    response.headers["Location"] = f"/item/{created_item.id}"
    return created_item


@router.get("/{item_id}", response_model=ItemResponse, status_code=HTTPStatus.OK)
async def get_item_by_id(item_id: int, conn: Connection = Depends(get_db_connection)):
    """Получение товара по id."""
    item = await get_item(conn, item_id)
    if not item or item.deleted:
        raise ItemNotFoundException(item_id)
    return {"id": item.id, **item.dict()}  # Добавлено поле `id` в ответ


@router.get("/", response_model=List[ItemResponse], status_code=HTTPStatus.OK)
async def get_items(
    offset: int = Query(0, ge=0, description="Смещение по списку"),
    limit: int = Query(10, gt=0, description="Ограничение на количество"),
    min_price: Optional[float] = Query(None, ge=0.0, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, ge=0.0, description="Максимальная цена"),
    show_deleted: bool = Query(False, description="Показывать ли удаленные товары"),
    conn: Connection = Depends(get_db_connection)
):
    """Получение списка товаров с фильтрацией."""
    items = await get_items_list(conn, offset, limit, min_price, max_price, show_deleted)
    return items


@router.put("/{item_id}", response_model=ItemResponse, status_code=HTTPStatus.OK)
async def update_item_by_id(
    item_id: int,
    item_update: ItemCreateRequest,  # PUT требует полного обновления
    conn: Connection = Depends(get_db_connection)
):
    """Замена товара по id (создание запрещено, только замена существующего)."""
    item = await get_item(conn, item_id)
    if not item:
        raise ItemNotFoundException(item_id)

    updated_item = await update_item(conn, item_id, item_update)
    return updated_item


@router.patch("/{item_id}", response_model=ItemResponse, status_code=HTTPStatus.OK)
async def partial_update_item_by_id(
    item_id: int,
    item_update: ItemUpdateRequest,
    conn: Connection = Depends(get_db_connection)
):
    """Частичное обновление товара по id (нельзя изменять поле deleted)."""
    item = await get_item(conn, item_id)
    if not item:
        raise ItemNotModifiedException(item_id)

    if item.deleted:
        # Изменение удаленного товара недопустимо
        raise ItemNotModifiedException(item_id)

    # Преобразуем в словарь текущие данные и обновляемые данные
    current_data = item.model_dump()
    update_data = item_update.model_dump()

    # Исключаем обновление поля deleted
    if "deleted" in update_data:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Поле 'deleted' нельзя изменять."
        )
    
    # Если данные не изменились, возвращаем статус 304 Not Modified
    if not any(current_data.get(key) != value for key, value in update_data.items()):
        raise ItemNotModifiedException(item_id)

    # Выполняем обновление данных
    updated_item = await update_item(conn, item_id, item_update)
    return updated_item


@router.delete("/{item_id}", status_code=HTTPStatus.OK)
async def delete_item_by_id(
    item_id: int,
    conn: Connection = Depends(get_db_connection)
):
    """Удаление товара по id (товар помечается как удаленный)."""
    item = await get_item(conn, item_id)
    if not item:
        raise ItemNotFoundException(item_id)

    if item.deleted:
        return {"detail": f"Товар с ID {item_id} уже помечен как удаленный."}

    await delete_item(conn, item_id)
    return {"detail": f"Товар с ID {item_id} помечен как удаленный."}
