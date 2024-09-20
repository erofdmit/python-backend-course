from http import HTTPStatus
from .math_api import MathAPI
from .utils import json_response, get_request_body, get_query_params
from .validation import validate_factorial, validate_fibonacci, validate_mean
from .calculations import calculate_factorial, calculate_fibonacci, calculate_mean

app = MathAPI()

@app.route("/factorial")
async def factorial(scope, receive, send):
    params = get_query_params(scope)
    n = validate_factorial(params.get('n'))
    if isinstance(n, HTTPStatus):
        await json_response(send, {"error": n.phrase}, status=n.value)
        return
    result = {"result": calculate_factorial(n)}
    await json_response(send, result)

@app.route("/fibonacci/{n}")
async def fibonacci(scope, receive, send):
    path_params = scope.get('path_params', {})
    n_str = path_params.get('n')
    n = validate_fibonacci(n_str)
    if isinstance(n, HTTPStatus):
        await json_response(send, {"error": n.phrase}, status=n.value)
        return
    result = {"result": calculate_fibonacci(n)}
    await json_response(send, result)


@app.route("/mean")
async def mean(scope, receive, send):
    body = await get_request_body(receive)
    if body is None:
        await json_response(send, {"error": "Unprocessable Entity"}, status=HTTPStatus.UNPROCESSABLE_ENTITY)
        return
    numbers = validate_mean(body)
    if isinstance(numbers, HTTPStatus):
        await json_response(send, {"error": numbers.phrase}, status=numbers.value)
        return
    result = {"result": calculate_mean(numbers)}
    await json_response(send, result)


# 404 handler
@app.default()
async def not_found(scope, receive, send):
    await json_response(send, {"error": "Not Found"}, status=HTTPStatus.NOT_FOUND.value)
