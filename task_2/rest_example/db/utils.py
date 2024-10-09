from typing import Any, Dict, List, Optional
from aiosqlite import Connection

async def fetch_one(conn: Connection, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
    """
    Выполняет SQL-запрос и возвращает одну строку в виде словаря.
    """
    async with conn.execute(query, params or ()) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

async def fetch_all(conn: Connection, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Выполняет SQL-запрос и возвращает все строки в виде списка словарей.
    """
    async with conn.execute(query, params or ()) as cursor:
        rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
