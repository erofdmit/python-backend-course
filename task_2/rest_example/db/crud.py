from typing import List, Optional
from aiosqlite import Connection
from ..models.cart import CartResponse, CartItem
from ..models.item import ItemResponse, ItemCreateRequest, ItemUpdateRequest


async def create_cart(conn: Connection) -> CartResponse:
    cursor = await conn.execute("INSERT INTO carts (price) VALUES (0.0)")
    await conn.commit()
    cart_id = cursor.lastrowid
    cursor = await conn.execute("SELECT * FROM carts WHERE id = ?", (cart_id,))
    row = await cursor.fetchone()

    columns = [column[0] for column in cursor.description]
    cart_data = dict(zip(columns, row))

    return CartResponse(**cart_data)


async def create_item(conn: Connection, item_data: ItemCreateRequest) -> ItemResponse:
    cursor = await conn.execute(
        "INSERT INTO items (name, price) VALUES (?, ?)",
        (item_data.name, item_data.price)
    )
    await conn.commit()
    item_id = cursor.lastrowid
    return ItemResponse(id=item_id, name=item_data.name, price=item_data.price, deleted=False)


async def get_item(conn: Connection, item_id: int) -> Optional[ItemResponse]:
    """Получение товара по id с проверкой на удаление."""
    async with conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None

        # Извлекаем названия столбцов
        columns = [column[0] for column in cursor.description]

        # Преобразуем строку в словарь с именами столбцов
        row_dict = dict(zip(columns, row))


    return ItemResponse(
        id=row_dict["id"],
        name=row_dict["name"],
        price=row_dict["price"],
        deleted=row_dict["deleted"]
    )


async def get_items_list(
    conn: Connection,
    offset: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    show_deleted: bool = False
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

    cursor = await conn.execute(query, tuple(params))
    rows = await cursor.fetchall()

    # Получаем имена столбцов
    columns = [column[0] for column in cursor.description]

    return [
        ItemResponse(**dict(zip(columns, row)))
        for row in rows
    ]


async def update_item(conn: Connection, item_id: int, item_update: ItemUpdateRequest) -> ItemResponse:
    query = "UPDATE items SET name = COALESCE(?, name), price = COALESCE(?, price) WHERE id = ? AND deleted = FALSE"
    await conn.execute(query, (item_update.name, item_update.price, item_id))
    await conn.commit()
    cursor = await conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = await cursor.fetchone()

    # Преобразование в словарь
    columns = [column[0] for column in cursor.description]
    item_data = dict(zip(columns, row))
    
    return ItemResponse(**item_data)


async def delete_item(conn: Connection, item_id: int):
    query = "UPDATE items SET deleted = TRUE WHERE id = ?"
    await conn.execute(query, (item_id,))
    await conn.commit()


async def get_cart(conn: Connection, cart_id: int) -> Optional[CartResponse]:
    """Получение корзины по id с информацией о товарах."""
    # Получение информации о корзине
    async with conn.execute("SELECT * FROM carts WHERE id = ?", (cart_id,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None  # Корзина не найдена

        # Извлечение названий столбцов для корзины
        cart_columns = [column[0] for column in cursor.description]

        # Преобразование строки корзины в словарь
        cart_row = dict(zip(cart_columns, row))

    # Получаем товары в корзине
    async with conn.execute(
        "SELECT ci.item_id, ci.quantity, ci.available, i.name, i.price "
        "FROM cart_items ci JOIN items i ON ci.item_id = i.id "
        "WHERE ci.cart_id = ? AND i.deleted = FALSE",
        (cart_id,)
    ) as cursor_items:
        # Извлечение названий столбцов
        item_columns = [column[0] for column in cursor_items.description]

        # Преобразование результатов в список словарей
        items_rows = [
            {column: value for column, value in zip(item_columns, row)}
            for row in await cursor_items.fetchall()
        ]

    # Преобразование строк в объекты CartItem
    items = [
        CartItem(
            id=item_row["item_id"],
            item=await get_item(conn, item_row["item_id"]),
            quantity=item_row["quantity"],
            available=item_row["available"]
        ) for item_row in items_rows
    ]

    return CartResponse(
        id=cart_row["id"],
        items=items,
        price=cart_row["price"]
    )


async def get_cart_list(
    conn: Connection,
    offset: int = 0,
    limit: int = 10,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_quantity: Optional[int] = None,
    max_quantity: Optional[int] = None
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

    cursor = await conn.execute(query, tuple(params))
    cart_rows = await cursor.fetchall()

    # Извлечение имен столбцов для carts
    cart_columns = [column[0] for column in cursor.description]
    carts = []

    for row in cart_rows:
        # Преобразование строки в словарь
        cart_row = dict(zip(cart_columns, row))
        cart_id = cart_row["id"]
        cart_price = cart_row["price"]

        items_cursor = await conn.execute(
            "SELECT cart_items.quantity, cart_items.available, items.id, items.name, items.price, items.deleted "
            "FROM cart_items JOIN items ON cart_items.item_id = items.id WHERE cart_items.cart_id = ?", (cart_id,)
        )
        
        # Извлечение имен столбцов для cart_items
        item_columns = [column[0] for column in items_cursor.description]

        items = [
            CartItem(
                item=ItemResponse(
                    id=item_row["id"],
                    name=item_row["name"],
                    price=item_row["price"],
                    deleted=item_row["deleted"]
                ),
                quantity=item_row["quantity"],
                available=item_row["available"]
            ) for item_row in [
                dict(zip(item_columns, row))
                for row in await items_cursor.fetchall()
            ]
        ]

        total_quantity = sum(item.quantity for item in items)
        if (min_quantity is not None and total_quantity < min_quantity) or (max_quantity is not None and total_quantity > max_quantity):
            continue

        carts.append(CartResponse(id=cart_id, items=items, price=cart_price))

    return carts


async def add_item_to_cart(conn: Connection, cart_id: int, item_id: int, quantity: int) -> Optional[CartResponse]:
    """Добавление товара в корзину с проверкой на удаление и подсчетом суммы."""
    # Получаем товар и проверяем, не удален ли он
    async with conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None

        # Извлекаем названия столбцов
        columns = [column[0] for column in cursor.description]
        item = dict(zip(columns, row))

        if item["deleted"]:
            raise ValueError(f"Товар '{item['name']}' помечен как удаленный и не может быть добавлен в корзину.")

    # Проверка наличия товара в корзине
    async with conn.execute("SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?", (cart_id, item_id)) as cursor:
        row = await cursor.fetchone()

        # Извлекаем названия столбцов
        columns = [column[0] for column in cursor.description]
        cart_item = dict(zip(columns, row)) if row else None

    if cart_item:
        # Если товар уже в корзине, увеличиваем его количество
        new_quantity = cart_item["quantity"] + quantity
        await conn.execute(
            "UPDATE cart_items SET quantity = ?, price = ? * quantity WHERE cart_id = ? AND item_id = ?",
            (new_quantity, item["price"], cart_id, item_id)
        )
    else:
        # Иначе добавляем новый товар в корзину с расчетом общей стоимости
        total_price = item["price"] * quantity
        await conn.execute(
            "INSERT INTO cart_items (cart_id, item_id, quantity, price) VALUES (?, ?, ?, ?)",
            (cart_id, item_id, quantity, total_price)
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
        (cart_id, cart_id)
    )

    await conn.commit()

    # Возвращаем обновленную корзину
    return await get_cart(conn, cart_id)


