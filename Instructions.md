# Инструкция
Все команды PowerShell выполняются из `C:\Users\egpoz\mle-model-production`.

## Этап 1. FastAPI
Python 3.10 соответствует среде модели; локально проверен также Python 3.12. Если venv уже создан, используйте его. Перед запуском освободите порт 8000: остановите Compose (`docker compose --env-file services/.env down`) или предыдущий Uvicorn.
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn services.ml_service.app:app --host 127.0.0.1 --port 8000
```
В другом терминале из той же директории:
```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body (Get-Content example.json -Raw)
.\.venv\Scripts\python.exe -m pytest -q
```
Swagger: http://localhost:8000/docs. Перед этапом 2 остановите Uvicorn сочетанием Ctrl+C.

## Этап 2. Docker
Docker Desktop должен работать. Порт 8000 должен быть свободен; работающий Compose остановите командой `docker compose --env-file services/.env down`.
```powershell
docker build -f Dockerfile_ml_service -t mle-model-production:local .
docker run --rm -d --name mle-production-audit-cli --env-file services/.env -p 127.0.0.1:8000:8000 mle-model-production:local
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/predict -Method Post -ContentType 'application/json' -Body (Get-Content example.json -Raw)
docker stop mle-production-audit-cli
```

## Этап 3. Docker Compose
Остановите отдельный контейнер или Uvicorn, если они занимают порт 8000. После старта дождитесь загрузки модели и готовности Grafana; при отказе соединения повторите проверку через несколько секунд.
```powershell
docker compose --env-file services/.env up -d --build
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:9090/-/ready
Invoke-RestMethod http://localhost:9090/api/v1/targets
Invoke-RestMethod http://localhost:3000/api/health
```
Порты задаются в services/.env. Prometheus: http://localhost:9090, Grafana: http://localhost:3000. Вход admin / student-local. Остановка только этого проекта: `docker compose --env-file services/.env down`. Volume Grafana сохраняется.

## Этап 4. Дашборд
Сначала запустите Compose по этапу 3 и подготовьте venv по этапу 1. Отдельный Uvicorn для этого этапа не нужен.
```powershell
.\.venv\Scripts\python.exe generate_load.py --count 300 --rate 2 --invalid-ratio 0.1
```
Для непрерывной нагрузки используйте `--count 0`, завершение Ctrl+C. Откройте http://localhost:3000/d/real-estate. Дашборд и datasource создаются автоматически. Для ручного импорта выберите dashboard.json; datasource должен иметь UID prometheus. Подождите минуту для расчёта rate, сравните графики до и после нагрузки. Полный настоящий снимок четырёх панелей сохранён в dashboard.jpg.
