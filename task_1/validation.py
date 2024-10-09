from http import HTTPStatus


def validate_factorial(n):
    if n is None or not n.lstrip("-").isdigit():
        return HTTPStatus.UNPROCESSABLE_ENTITY
    n = int(n)
    if n < 0:
        return HTTPStatus.BAD_REQUEST
    return n


def validate_fibonacci(n_str):
    if n_str is None or not n_str.lstrip("-").isdigit():
        return HTTPStatus.UNPROCESSABLE_ENTITY
    n = int(n_str)
    if n < 0:
        return HTTPStatus.BAD_REQUEST
    return n


def validate_mean(numbers):
    if numbers is None:
        return HTTPStatus.UNPROCESSABLE_ENTITY
    if not isinstance(numbers, list) or not all(
        isinstance(num, (int, float)) for num in numbers
    ):
        return HTTPStatus.UNPROCESSABLE_ENTITY
    if not numbers:
        return HTTPStatus.BAD_REQUEST
    return numbers
