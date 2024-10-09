import aiosqlite
from contextlib import asynccontextmanager
DATABASE_PATH = "./database.db"

async def get_db_connection():
    """Возвращает асинхронное соединение с базой данных."""
    return await aiosqlite.connect(DATABASE_PATH)

async def init_db():
    """Инициализация базы данных, создание таблиц."""
    async with aiosqlite.connect(DATABASE_PATH) as conn:  # Используем явное создание подключения
        # Создание таблицы товаров
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                deleted BOOLEAN DEFAULT FALSE
            )
        """)
        # Создание таблицы корзин
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id INTEGER PRIMARY KEY,
                price REAL DEFAULT 0.0
            )
        """)
        # Создание таблицы элементов корзины
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY,
                cart_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                available BOOLEAN DEFAULT TRUE,
                price REAL NOT NULL,
                FOREIGN KEY(cart_id) REFERENCES carts(id),
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        """)
        # Применение изменений в базе данных
        await conn.commit()
