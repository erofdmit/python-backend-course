from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from http import HTTPStatus

# Исключения для товаров
class ItemNotFoundException(HTTPException):
    def __init__(self, item_id: int):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=f"Товар с ID {item_id} не найден или удален.")

class ItemNotModifiedException(HTTPException):
    def __init__(self, item_id: int):
        super().__init__(status_code=HTTPStatus.NOT_MODIFIED, detail=f"Товар с ID {item_id} не был изменен.")

# Исключения для корзин
class CartNotFoundException(HTTPException):
    def __init__(self, cart_id: int):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=f"Корзина с ID {cart_id} не найдена.")

# Исключение для валидации параметров корзины
class CartValidationException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=detail)

# Обработчик исключений HTTPException
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Обработчик исключений валидации входных данных
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"detail": "Ошибка валидации входных данных", "errors": exc.errors()}
    )
