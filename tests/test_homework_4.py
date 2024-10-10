import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from task_4.demo_service.api.main import create_app
from task_4.demo_service.core.users import UserService, UserInfo, UserRole
from datetime import datetime


# Фикстура для инициализации приложения
@pytest.fixture(scope="module")
def app() -> FastAPI:
    app_instance = create_app()
    return app_instance


# Создание синхронного клиента для тестирования
@pytest.fixture(scope="module")
def test_client(app: FastAPI):
    return TestClient(app)


# Асинхронный клиент для тестирования
@pytest.fixture(scope="module")
async def async_client(app: FastAPI):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Фикстура для явной инициализации `user_service` перед тестами
@pytest.fixture(scope="module", autouse=True)
def initialize_user_service(app: FastAPI):
    # Инициализация UserService и добавление его в state
    user_service = UserService(
        password_validators=[
            lambda pwd: len(pwd) > 8,
            lambda pwd: any(char.isdigit() for char in pwd),
        ]
    )
    user_service.register(
        UserInfo(
            username="admin",
            name="admin",
            birthdate=datetime.fromtimestamp(0.0),
            role=UserRole.ADMIN,
            password="superSecretAdminPassword123",
        )
    )
    app.state.user_service = user_service


# Фикстура для получения `user_service` из состояния приложения
@pytest.fixture(scope="module")
def user_service(app: FastAPI) -> UserService:
    # Проверяем наличие `user_service` в состоянии приложения
    if not hasattr(app.state, "user_service"):
        raise RuntimeError("UserService is not initialized in app.state")
    return app.state.user_service


# Тест успешной регистрации и получения пользователя
@pytest.mark.xfail()
def test_register_and_get_user(test_client, user_service):
    # Регистрация пользователя
    response = test_client.post(
        "/user-register",
        json={
            "username": "testuser",
            "name": "Test User",
            "birthdate": "2000-01-01T00:00:00",
            "password": "validPassword123",
        },
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "testuser"

    # Получение зарегистрированного пользователя по id
    response = test_client.post(
        "/user-get",
        params={"id": user_data["uid"]},
        headers={"Authorization": "Basic YWRtaW46c3VwZXJTZWNyZXRBZG1pblBhc3N3b3JkMTIz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == user_data["uid"]
    assert data["username"] == "testuser"
    assert data["name"] == "Test User"


# Тесты регистрации пользователей с различными ошибками
@pytest.mark.xfail()
@pytest.mark.parametrize(
    "json_data, expected_status, expected_detail",
    [
        # Пароль слишком короткий
        (
            {
                "username": "user2",
                "name": "User Two",
                "birthdate": "2000-01-01T00:00:00",
                "password": "short",
            },
            400,
            "invalid password",
        ),
        # Отсутствует имя
        (
            {
                "username": "user3",
                "birthdate": "2000-01-01T00:00:00",
                "password": "validPassword123",
            },
            422,
            None,
        ),
        # Отсутствует пароль
        (
            {
                "username": "user3",
                "name": "User Three",
                "birthdate": "2000-01-01T00:00:00",
            },
            422,
            None,
        ),
        # Неправильный формат даты
        (
            {
                "username": "user4",
                "name": "User Four",
                "birthdate": "invalid-date",
                "password": "validPassword123",
            },
            422,
            None,
        ),
        # Дублирующийся username
        (
            {
                "username": "duplicateUser",
                "name": "Duplicate User",
                "birthdate": "2000-01-01T00:00:00",
                "password": "Password12345",
            },
            400,
            "username is already taken",
        ),
    ],
)
def test_register_user_invalid_scenarios(test_client, user_service, json_data, expected_status, expected_detail):
    # Предварительная регистрация пользователя с дублирующимся именем
    if json_data.get("username") == "duplicateUser":
        user_service.register(
            UserInfo(
                username="duplicateUser",
                name="Duplicate User",
                birthdate="2000-01-01T00:00:00",
                password="Password12345",
            )
        )

    response = test_client.post("/user-register", json=json_data)
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json() == {"detail": expected_detail}


# Тесты получения пользователя с неправильными параметрами
@pytest.mark.xfail()
@pytest.mark.parametrize(
    "params, expected_status, expected_detail",
    [
        # Ни id, ни username не указаны
        ({}, 400, "neither id nor username are provided"),
        # И id, и username указаны
        ({"id": 1, "username": "user"}, 400, "both id and username are provided"),
    ],
)
def test_get_user_invalid_scenarios(test_client, params, expected_status, expected_detail):
    response = test_client.post(
        "/user-get",
        params=params,
        headers={"Authorization": "Basic YWRtaW46c3VwZXJTZWNyZXRBZG1pblBhc3N3b3JkMTIz"},
    )
    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}


# Тесты получения несуществующего пользователя
@pytest.mark.xfail()
@pytest.mark.parametrize(
    "params, expected_status",
    [
        # Попытка получить несуществующего пользователя по id
        ({"id": 9999}, 404),
        # Попытка получить несуществующего пользователя по username
        ({"username": "unknownUser"}, 404),
    ],
)
def test_get_user_not_found(test_client, params, expected_status):
    response = test_client.post(
        "/user-get",
        params=params,
        headers={"Authorization": "Basic YWRtaW46c3VwZXJTZWNyZXRBZG1pblBhc3N3b3JkMTIz"},
    )
    assert response.status_code == expected_status


# Тесты повышения прав пользователя с различными ошибками
@pytest.mark.xfail()
@pytest.mark.parametrize(
    "params, headers, expected_status, expected_detail",
    [
        # Пользователь не найден
        ({"id": 9999}, {"Authorization": "Basic YWRtaW46c3VwZXJTZWNyZXRBZG1pblBhc3N3b3JkMTIz"}, 400, "user not found"),
        # Пользователь без прав администратора пытается повысить права
        ({"id": 1}, {"Authorization": "Basic dXNlcjpQYXNzd29yZDEyMw=="}, 401, None),
        # Без авторизации
        ({"id": 1}, {}, 401, None),
    ],
)
def test_promote_user_invalid_scenarios(test_client, params, headers, expected_status, expected_detail):
    response = test_client.post("/user-promote", params=params, headers=headers)
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json() == {"detail": expected_detail}
