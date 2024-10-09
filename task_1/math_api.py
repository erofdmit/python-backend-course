from http import HTTPStatus

class MathAPI:
    def __init__(self):
        self.routes = {}
        self.default_handler = None

    def route(self, path):
        def wrapper(func):
            self.routes[path] = func
            return func
        return wrapper

    def default(self):
        def wrapper(func):
            self.default_handler = func
            return func
        return wrapper

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            # Обработка HTTP запросов, проверка наличия 'path' и 'method'
            path = scope.get('path')
            method = scope.get('method')

            if path is None or method is None:
                await self._send_response(send, {"error": "Invalid request"}, HTTPStatus.BAD_REQUEST)
                return

            # Проверка маршрутов с параметрами {n}
            for route_path, handler in self.routes.items():
                if '{n}' in route_path:
                    base_route = route_path.replace('/{n}', '')
                    if path.startswith(base_route):
                        path_param = path[len(base_route) + 1:]
                        scope['path_params'] = {'n': path_param}
                        await handler(scope, receive, send)
                        return

            # Обработка маршрутов без параметров
            if path in self.routes:
                await self.routes[path](scope, receive, send)
            elif self.default_handler is not None:
                await self.default_handler(scope, receive, send)
            else:
                await self._send_response(send, {"error": "Not Found"}, HTTPStatus.NOT_FOUND)
        elif scope['type'] == 'lifespan':
            # Обработка жизненного цикла приложения
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    break
        else:
            await self._send_response(send, {"error": f"Unsupported scope type: {scope['type']}"}, HTTPStatus.BAD_REQUEST)

    async def _send_response(self, send, data, status):
        """Функция для отправки ответа с заданным статусом."""
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [(b'content-type', b'application/json')],
        })
        await send({
            'type': 'http.response.body',
            'body': bytes(str(data), 'utf-8'),
        })
