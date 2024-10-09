import json


async def json_response(send, data, status=200):
    response = {
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json")],
    }
    await send(response)
    await send(
        {
            "type": "http.response.body",
            "body": json.dumps(data).encode("utf-8"),
        }
    )


async def get_request_body(receive):
    body = await receive()
    if not body.get("body"):
        return None
    return json.loads(body["body"].decode("utf-8"))


def get_query_params(scope):
    query_string = scope["query_string"].decode("utf-8")
    params = {}
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value
        else:
            params[param] = None
    return params
