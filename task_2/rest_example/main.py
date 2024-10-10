from contextlib import asynccontextmanager
import logging
import os
import random
import time
from typing import Optional
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.middleware.cors import CORSMiddleware
import httpx
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from opentelemetry.propagate import inject
from .utils import PrometheusMiddleware, metrics, setting_otlp
from .routers import cart, item, chat, client
from .errors import http_exception_handler, validation_exception_handler
from opentelemetry.propagate import inject
from .db.db_engine import init_db 

APP_NAME = "fastapi_app"
EXPOSE_PORT = 8000
OTLP_GRPC_ENDPOINT = "http://tempo:4317"

@asynccontextmanager
async def lifespan(app: FastAPI):
    headers = {}
    inject(headers)
    logging.critical(headers)
    await init_db()
    yield

app = FastAPI(
    debug=False,
    title="Shop API",
    openapi_url="/api/v2/openapi.json",
    docs_url="/docs",
    redoc_url=None,
    swagger_ui_parameters={"syntaxHighlight": False},
    lifespan=lifespan,
)

@app.get("/", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Документация",
        redoc_js_url="/static/redoc.standalone.js",
    )


# Добавление CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Обработка исключений
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Подключение роутеров
app.include_router(router=client.router)
app.include_router(router=chat.router)
app.include_router(router=item.router)
app.include_router(router=cart.router)

# Setting metrics middleware
app.add_middleware(PrometheusMiddleware, app_name=APP_NAME)
Instrumentator().instrument(app).expose(app)

# Setting OpenTelemetry exporter
setting_otlp(app, APP_NAME, OTLP_GRPC_ENDPOINT)


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


log_config = uvicorn.config.LOGGING_CONFIG
log_config["formatters"]["access"][
    "fmt"
] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"

