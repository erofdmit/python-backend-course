from locust import HttpUser, TaskSet, task, between
import random
from uuid import uuid4


class CartTasks(TaskSet):
    cart_ids = []

    @task
    def create_cart(self):
        """Создать новую корзину и сохранить ее ID для дальнейших операций."""
        response = self.client.post("/cart/")
        if response.status_code == 201:
            cart_id = response.json().get("id")
            if cart_id:
                self.cart_ids.append(cart_id)

    @task
    def get_cart(self):
        """Получить случайную корзину по ID."""
        if self.cart_ids:
            cart_id = random.choice(self.cart_ids)
            self.client.get(f"/cart/{cart_id}")

    @task
    def get_cart_list(self):
        """Получить список корзин с рандомизированными фильтрами."""
        params = {
            "offset": random.randint(0, 10),
            "limit": random.randint(5, 20),
            "min_price": round(random.uniform(0.0, 50.0), 2),
            "max_price": round(random.uniform(50.0, 200.0), 2),
            "min_quantity": random.randint(0, 5),
            "max_quantity": random.randint(5, 50),
        }
        self.client.get("/cart/", params=params)

    @task
    def add_item_to_cart(self):
        """Добавить случайный товар в корзину."""
        if self.cart_ids:
            cart_id = random.choice(self.cart_ids)
            item_id = random.randint(1, 100)  # Предполагается, что есть товары с ID от 1 до 100
            self.client.post(f"/cart/{cart_id}/add/{item_id}", params={"quantity": random.randint(1, 5)})


class ItemTasks(TaskSet):
    item_ids = []

    @task
    def create_item(self):
        """Создать новый товар и сохранить его ID для дальнейших операций."""
        item_data = {
            "name": f"Item-{uuid4()}",
            "description": "Sample description",
            "price": round(random.uniform(10.0, 100.0), 2),
            "quantity": random.randint(1, 100)
        }
        response = self.client.post("/item/", json=item_data)
        if response.status_code == 201:
            item_id = response.json().get("id")
            if item_id:
                self.item_ids.append(item_id)

    @task
    def get_item(self):
        """Получить случайный товар по ID."""
        if self.item_ids:
            item_id = random.choice(self.item_ids)
            self.client.get(f"/item/{item_id}")

    @task
    def get_item_list(self):
        """Получить список товаров с рандомизированными фильтрами."""
        params = {
            "offset": random.randint(0, 10),
            "limit": random.randint(5, 20),
            "min_price": round(random.uniform(0.0, 50.0), 2),
            "max_price": round(random.uniform(50.0, 200.0), 2),
            "show_deleted": random.choice([True, False])
        }
        self.client.get("/item/", params=params)


class ChatTasks(TaskSet):
    chat_ids = []

    @task
    def create_chat(self):
        """Создать новый чат и сохранить его ID для дальнейших операций."""
        response = self.client.post("/chat/")
        if response.status_code == 201:
            chat_id = response.json().get("chat_id")
            if chat_id:
                self.chat_ids.append(chat_id)

    @task
    def publish_message(self):
        """Отправить случайное сообщение в случайный чат."""
        if self.chat_ids:
            chat_id = random.choice(self.chat_ids)
            message = {"message": f"Hello from Locust {uuid4()}"}
            self.client.post(f"/chat/publish/{chat_id}", json=message)


class WebsiteUser(HttpUser):
    # Время ожидания между запросами от каждого пользователя
    wait_time = between(1, 10)

    # Задачи, которые выполняет пользователь
    tasks = {CartTasks: 2, ItemTasks: 2, ChatTasks: 1}
