import requests
import time
import json
import os

# Настройки из переменных окружения
PROMETHEUS_URL = "http://127.0.0.1:9090/api/v1/query"
GRAFANA_URL = "http://127.0.0.1:3000"
GRAFANA_API_KEY = "glsa_6kfvbkfIOtsBYIgsuI6ArYzJ5XteBMLE_5562b039"
OUTPUT_FILE = "./metrics_report.json"  # Изменил путь на локальный для проверки

# Запросы к метрикам Prometheus
QUERY_RPS = 'rate(http_requests_total[5m])'
QUERY_SUCCESS_RATE = 'sum(rate(http_requests_total{status=~"2.."}[5m])) / sum(rate(http_requests_total[5m])) * 100'


def get_prometheus_metric(query):
    """Выполняет запрос к Prometheus и возвращает значение метрики."""
    try:
        print(f"Запрос к Prometheus: {query}")
        response = requests.get(PROMETHEUS_URL, params={'query': query})
        response.raise_for_status()  # Если код возврата не 200, выбросить исключение
        result = response.json().get('data', {}).get('result', [])
        print(f"Полученные данные от Prometheus: {result}")
        return result
    except Exception as e:
        print(f"Ошибка при запросе к Prometheus: {e}")
        return []  # Возврат пустого результата в случае ошибки


def get_grafana_dashboard_image(dashboard_uid, panel_id, output_path):
    """Получает изображение панели Grafana через API и сохраняет его в файл."""
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
    }
    params = {
        "orgId": 1,
        "panelId": panel_id,
        "tz": "UTC",
    }
    image_url = f"{GRAFANA_URL}/render/d-solo/{dashboard_uid}/panel_id"
    print(f"Запрос изображения панели Grafana: {image_url}")

    try:
        response = requests.get(image_url, headers=headers, params=params, stream=True)
        response.raise_for_status()

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Изображение панели Grafana сохранено: {output_path}")
    except Exception as e:
        print(f"Ошибка при получении изображения из Grafana: {e}")


def export_grafana_dashboard(dashboard_uid, output_path):
    """Экспортирует дашборд Grafana в JSON формат и сохраняет его на локальный диск."""
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
        "Content-Type": "application/json"
    }
    export_url = f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}"
    print(f"Запрос на экспорт дашборда Grafana: {export_url}")

    try:
        response = requests.get(export_url, headers=headers)
        response.raise_for_status()
        dashboard_json = response.json()

        with open(output_path, 'w') as f:
            json.dump(dashboard_json, f, indent=4)
        print(f"Дашборд Grafana успешно экспортирован и сохранен в {output_path}")
    except Exception as e:
        print(f"Ошибка при экспорте дашборда Grafana: {e}")


def get_active_panels(dashboard_uid):
    """Получает список активных панелей с дашборда Grafana."""
    headers = {
        "Authorization": f"Bearer {GRAFANA_API_KEY}",
        "Content-Type": "application/json"
    }
    dashboard_url = f"{GRAFANA_URL}/api/dashboards/uid/{dashboard_uid}"
    print(f"Запрос на получение данных дашборда: {dashboard_url}")

    try:
        response = requests.get(dashboard_url, headers=headers)
        response.raise_for_status()
        dashboard_data = response.json()
        panels = dashboard_data.get("dashboard", {}).get("panels", [])

        # Извлекаем ID всех активных панелей
        active_panel_ids = [panel['id'] for panel in panels]
        print(f"Список ID активных панелей: {active_panel_ids}")
        return active_panel_ids
    except Exception as e:
        print(f"Ошибка при получении активных панелей: {e}")
        return []


def save_metrics_to_file(file_path, data):
    """Сохраняет метрики в JSON файл."""
    try:
        print(f"Сохранение метрик в файл: {file_path}")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Метрики успешно сохранены в {file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении метрик: {e}")


def collect_metrics():
    """Собирает метрики с определенным интервалом времени и сохраняет их в файл."""
    metrics_data = {"rps": [], "success_rate": []}
    time.sleep(10)
    for i in range(15):
        # Сбор метрик каждые 60 секунд в течение 15 минут
        print(f"Сбор метрик. Итерация {i+1} из 15...")
        rps = get_prometheus_metric(QUERY_RPS)
        success_rate = get_prometheus_metric(QUERY_SUCCESS_RATE)
        metrics_data["rps"].append(rps)
        metrics_data["success_rate"].append(success_rate)
        time.sleep(60)
        

    save_metrics_to_file(OUTPUT_FILE, metrics_data)
    print(f"Метрики успешно собраны и сохранены в {OUTPUT_FILE}")
    
    # Получение активных панелей с дашборда
    dashboard_uid = "fastapi-observability"
    active_panels = get_active_panels(dashboard_uid)

    # Получение изображений активных панелей Grafana
    for panel_id in active_panels:
        get_grafana_dashboard_image(dashboard_uid, panel_id, f"./grafana_boards/panel_{panel_id}.png")


if __name__ == "__main__":
    collect_metrics()
