#!/bin/bash

# Запуск docker-compose в фоновом режиме (поднимает сервисы)
echo "Запуск docker-compose сервисов..."
docker plugin install grafana/loki-docker-driver:2.9.2 --alias loki --grant-all-permissions
docker-compose up -d

# Дождаться запуска всех сервисов в docker-compose
echo "Ожидание запуска сервисов..."
sleep 10  # Пауза на 10 секунд для инициализации сервисов

# Запуск Locust локально
echo "Запуск Locust..."
locust -f ./locust/locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 15m &

# Запуск сборщика метрик
echo "Запуск сборщика метрик..."
python3 ./metrics_collector/metrics_colleсtor.py &

# Ожидание завершения всех фоновых процессов
wait
sleep 10
# Завершение работы docker-compose сервисов
echo "Завершение работы сервисов..."
docker-compose down
