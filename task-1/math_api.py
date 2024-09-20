class MathAPI:
    def __init__(self):
        self.routes = {}

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
        path = scope['path']
        method = scope['method']

        for route_path, handler in self.routes.items():
            if '{n}' in route_path:
                base_route = route_path.replace('/{n}', '')
                if path.startswith(base_route):
                    path_param = path[len(base_route) + 1:]
                    scope['path_params'] = {'n': path_param}
                    await handler(scope, receive, send)
                    return

        if path in self.routes:
            await self.routes[path](scope, receive, send)
        else:
            await self.default_handler(scope, receive, send)
