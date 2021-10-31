# Пример окружения для нагрузочного тестирования
---
Установка doit
`pip install doit`


Запуск приложения
`doit up`

Запуск мониторингов
`doit monitoring`

---
После создание графаны добавить основные такие панели

1. CPU USAGE {{name}}
  - rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_project="load",container_label_com_docker_compose_service="app"}[$__interval])
  - rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_project="load",container_label_com_docker_compose_service="postgres"}[$__interval])
  - rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_project="load",container_label_com_docker_compose_service="redis"}[$__interval])
2. RPS {{endpoint}}
  - sum by(endpoint)(rate(http_requests_total{job="app"}[$__interval]))
3. PG LOCKS {{mode}}
  - rate(postgres_locks_in_flight{job="postgres"}[$__interval])

---
