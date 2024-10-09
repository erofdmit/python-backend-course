from typing import List, Optional
from aiosqlite import Connection
from ..models.cart import CartResponse, CartItem
from ..models.item import ItemResponse, ItemCreateRequest, ItemUpdateRequest
from .utils import fetch_one, fetch_all


async def create_cart(conn: Connection) -> CartResponse:
    await conn.execute("INSERT INTO carts (price) VALUES (0.0)")
    await conn.commit()
    cart_id = conn.last_insert_rowid
    cart_data = await fetch_one(conn, "SELECT * FROM carts WHERE id = ?", (cart_id,))
    if cart_data is None:
        raise ValueError("Не удалось создать корзину.")
    return CartResponse(**cart_data)


async def create_item(conn: Connection, item_data: ItemCreateRequest) -> ItemResponse:
    await conn.execute(
        "INSERT INTO items (name, price) VALUES (?, ?)",
        (item_data.name, item_data.price),
    )
    await conn.commit()
    item_id = conn.last_insert_rowid
    return ItemResponse(
        id=item_id, name=item_data.name, price=item_data.price, deleted=False
    )


async def get_item(conn: Connection, item_id: int) -> Optional[ItemResponse]:
    """Получение товара по id с проверкой на удаление."""
    row = await fetch_one(conn, "SELECT * FROM items WHERE id = ?", (item_id,))
    if row is None:
        return None
    return ItemResponse(**row)


async def get_items_list(
    conn: Connection,
    offset: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    show_deleted: bool = False,
) -> List[ItemResponse]:
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    if not show_deleted:
        query += " AND deleted = ?"
        params.append(False)

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = await fetch_all(conn, query, tuple(params))
    return [ItemResponse(**row) for row in rows]


async def update_item(
    conn: Connection, item_id: int, item_update: ItemUpdateRequest
) -> Optional[ItemResponse]:
    query = """
        UPDATE items 
        SET name = COALESCE(?, name), 
            price = COALESCE(?, price) 
        WHERE id = ? AND deleted = FALSE
    """
    await conn.execute(query, (item_update.name, item_update.price, item_id))
    await conn.commit()
    row = await fetch_one(conn, "SELECT * FROM items WHERE id = ?", (item_id,))
    if row is None:
        return None
    return ItemResponse(**row)


async def delete_item(conn: Connection, item_id: int):
    await conn.execute("UPDATE items SET deleted = TRUE WHERE id = ?", (item_id,))
    await conn.commit()


async def get_cart(conn: Connection, cart_id: int) -> Optional[CartResponse]:
    """Получение корзины по id с информацией о товарах."""
    cart_row = await fetch_one(conn, "SELECT * FROM carts WHERE id = ?", (cart_id,))
    if cart_row is None:
        return None  # Корзина не найдена

    # Получаем товары в корзине
    items_query = """
        SELECT ci.item_id, ci.quantity, ci.available, i.name, i.price 
        FROM cart_items ci 
        JOIN items i ON ci.item_id = i.id 
        WHERE ci.cart_id = ? AND i.deleted = FALSE
    """
    items_rows = await fetch_all(conn, items_query, (cart_id,))

    # Преобразование строк в объекты CartItem
    items = [
        CartItem(
            id=item_row["item_id"],
            item=ItemResponse(
                id=item_row["item_id"],
                name=item_row["name"],
                price=item_row["price"],
                deleted=False,  # Предполагаем, что deleted = FALSE
            ),
            quantity=item_row["quantity"],
            available=item_row["available"],
        )
        for item_row in items_rows
    ]

    return CartResponse(id=cart_row["id"], items=items, price=cart_row["price"])


async def get_cart_list(
    conn: Connection,
    offset: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_quantity: Optional[int] = None,
    max_quantity: Optional[int] = None,
) -> List[CartResponse]:
    query = "SELECT * FROM carts WHERE 1=1"
    params = []

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cart_rows = await fetch_all(conn, query, tuple(params))
    carts = []

    for cart_row in cart_rows:
        cart_id = cart_row["id"]
        cart_price = cart_row["price"]

        items_query = """
            SELECT cart_items.quantity, cart_items.available, items.id, items.name, items.price, items.deleted
            FROM cart_items 
            JOIN items ON cart_items.item_id = items.id 
            WHERE cart_items.cart_id = ?
        """
        items_rows = await fetch_all(conn, items_query, (cart_id,))

        items = [
            CartItem(
                item=ItemResponse(
                    id=item_row["id"],
                    name=item_row["name"],
                    price=item_row["price"],
                    deleted=item_row["deleted"],
                ),
                quantity=item_row["quantity"],
                available=item_row["available"],
            )
            for item_row in items_rows
        ]

        total_quantity = sum(item.quantity for item in items)
        if (min_quantity is not None and total_quantity < min_quantity) or (
            max_quantity is not None and total_quantity > max_quantity
        ):
            continue

        carts.append(CartResponse(id=cart_id, items=items, price=cart_price))

    return carts


async def add_item_to_cart(
    conn: Connection, cart_id: int, item_id: int, quantity: int
) -> Optional[CartResponse]:
    """Добавление товара в корзину с проверкой на удаление и подсчетом суммы."""
    # Получаем товар и проверяем, не удален ли он
    item = await fetch_one(conn, "SELECT * FROM items WHERE id = ?", (item_id,))
    if item is None:
        return None

    if item["deleted"]:
        raise ValueError(
            f"Товар '{item['name']}' помечен как удаленный и не может быть добавлен в корзину."
        )

    # Проверка наличия товара в корзине
    cart_item = await fetch_one(
        conn,
        "SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?",
        (cart_id, item_id),
    )

    if cart_item:
        # Если товар уже в корзине, увеличиваем его количество
        new_quantity = cart_item["quantity"] + quantity
        await conn.execute(
            "UPDATE cart_items SET quantity = ?, price = ? * quantity WHERE cart_id = ? AND item_id = ?",
            (new_quantity, item["price"], cart_id, item_id),
        )
    else:
        # Иначе добавляем новый товар в корзину с расчетом общей стоимости
        total_price = item["price"] * quantity
        await conn.execute(
            "INSERT INTO cart_items (cart_id, item_id, quantity, price) VALUES (?, ?, ?, ?)",
            (cart_id, item_id, quantity, total_price),
        )

    # Обновляем поле `price` в таблице `carts`
    await conn.execute(
        """
        UPDATE carts
        SET price = (
            SELECT COALESCE(SUM(price), 0)
            FROM cart_items
            WHERE cart_id = ?
        )
        WHERE id = ?
        """,
        (cart_id, cart_id),
    )

    await conn.commit()

    # Возвращаем обновленную корзину
    return await get_cart(conn, cart_id)
