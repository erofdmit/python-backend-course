from fastapi import APIRouter, HTTPException, Depends, Response, Query
from typing import List, Optional
from aiosqlite import Connection
from http import HTTPStatus
from ..models.cart import CartResponse, CartCreateRequest, CartItem
from ..models.item import ItemResponse
from ..db.db_engine import get_db_connection
from ..db.crud import create_cart, get_cart, get_cart_list, add_item_to_cart, get_item
from ..errors import CartNotFoundException, ItemNotFoundException, CartValidationException

router = APIRouter(prefix='/cart')

@router.post("/", response_model=CartResponse, status_code=HTTPStatus.CREATED)
async def create_new_cart(response: Response, conn: Connection = Depends(get_db_connection)):
    """Создание новой корзины."""
    cart = await create_cart(conn)
    response.headers["Location"] = f"/cart/{cart.id}"
    return cart


@router.get("/{cart_id}", response_model=CartResponse, status_code=HTTPStatus.OK)
async def get_cart_by_id(cart_id: int, conn: Connection = Depends(get_db_connection)):
    """Получение корзины по id."""
    cart = await get_cart(conn, cart_id)
    if not cart:
        raise CartNotFoundException(cart_id)
    return cart


@router.get("/", response_model=List[CartResponse], status_code=HTTPStatus.OK)
async def get_carts(
    offset: int = Query(0, ge=0, description="Смещение по списку"),
    limit: int = Query(10, gt=0, description="Ограничение на количество"),
    min_price: Optional[float] = Query(None, ge=0.0, description="Минимальная цена корзины"),
    max_price: Optional[float] = Query(None, ge=0.0, description="Максимальная цена корзины"),
    min_quantity: Optional[int] = Query(None, ge=0, description="Минимальное общее количество товаров"),
    max_quantity: Optional[int] = Query(None, ge=0, description="Максимальное общее количество товаров"),
    conn: Connection = Depends(get_db_connection)
):
    """Получение списка корзин с фильтрацией по цене и количеству товаров."""
    carts = await get_cart_list(conn, offset, limit, min_price, max_price, min_quantity, max_quantity)
    return carts


@router.post("/{cart_id}/add/{item_id}", response_model=CartResponse, status_code=HTTPStatus.OK)
async def add_item_to_cart_endpoint(
    cart_id: int,
    item_id: int,
    quantity: Optional[int] = Query(1, gt=0, description="Количество добавляемого товара"),
    conn: Connection = Depends(get_db_connection)
):
    """Добавление товара с item_id в корзину с cart_id. Увеличивает количество товара, если он уже есть."""
    # Получение корзины по id
    cart = await get_cart(conn, cart_id)
    if not cart:
        raise CartNotFoundException(cart_id)

    # Получение товара по id
    item = await get_item(conn, item_id)
    if not item or item.deleted:
        raise ItemNotFoundException(item_id)

    # Добавление товара в корзину
    updated_cart = await add_item_to_cart(conn, cart_id, item_id, quantity)
    return updated_cart
