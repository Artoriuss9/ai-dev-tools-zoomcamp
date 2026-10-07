# PUBG Match Analytics

FastAPI-приложение получает последние матчи игрока через PUBG API, сохраняет
статистику в SQLite и показывает аналитику в веб-интерфейсе. Ключ API хранится
только в локальном `.env` и не включается в Docker-образ.

## Локальный запуск через Docker Compose

Нужны Docker Desktop и Docker Compose. В PowerShell из папки проекта:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Укажите настоящий `PUBG_API_KEY`, затем запустите приложение и стек
наблюдаемости:

```powershell
docker compose up --build -d --wait
```

- Приложение: <http://127.0.0.1:8000/>
- Swagger: <http://127.0.0.1:8000/docs>
- Liveness: <http://127.0.0.1:8000/health>
- Readiness (включая проверку SQLite): <http://127.0.0.1:8000/ready>
- Grafana: <http://127.0.0.1:3000/> (`admin` / `admin`, только для локальной разработки)
- Prometheus: <http://127.0.0.1:9090/>

Grafana автоматически настраивает источники Prometheus, Loki и Tempo. Метрики,
логи и трассировки можно смотреть в разделе Explore. HTTP-логи приложения
пишутся в JSON в stdout:

```powershell
docker compose logs -f app
```

SQLite хранится в именованном Docker volume и переживает пересоздание
контейнеров. Остановить стек, сохранив данные:

```powershell
docker compose down
```

Для окружения с PostgreSQL укажите `DATABASE_URL` в формате
`postgresql+psycopg://user:password@host:5432/database`. PostgreSQL драйвер
входит в runtime-зависимости; в Docker Compose SQLite остаётся локальным
значением по умолчанию.

## Локальный запуск без Docker

Нужен Python 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Укажите PUBG_API_KEY в .env
uvicorn backend.app.main:app --reload
```

При локальном запуске без OTLP endpoint приложение пишет JSON-логи в консоль.
Для отправки телеметрии задайте `OTEL_EXPORTER_OTLP_ENDPOINT`; по умолчанию
Compose направляет её в локальный OpenTelemetry Collector.

## Тесты и CI

Из папки `pubg-analytics` выполните:

```powershell
python -m pip install -r requirements-dev.txt
pytest -q
```

Тесты не обращаются к реальному PUBG API и используют изолированную SQLite.
GitHub Actions устанавливает dev-зависимости, запускает тесты и собирает
Docker-образ для push и pull request. Образ приложения устанавливает только
runtime-зависимости из `requirements.txt`.

## API

`POST /analyze` принимает `{"nickname":"PlayerName"}`. Успешный ответ включает
игрока, сводную статистику, матчи и аналитические insights. Ошибки возвращаются
в формате `{ "error": { "code": "...", "message": "..." } }`.

`GET /health` — liveness-проверка процесса. `GET /ready` выполняет запрос к
базе данных и возвращает HTTP 503, если она недоступна.

OpenAPI-контракт хранится в [`openapi.yaml`](openapi.yaml) и генерируется из
FastAPI-схем:

```powershell
python ops/export_openapi.py
```

## Архитектура, тесты и AI workflow

Backend размещён в `backend/app/`, браузерный frontend — в `frontend/`, продуктовые
требования — в [`product-spec.md`](product-spec.md). [Архитектура](docs/architecture.md)
описывает взаимодействие UI, API, PUBG API, базы и observability-стека.
[`AGENTS.md`](AGENTS.md) содержит проектные инструкции, а
[AI workflow](docs/ai-workflow.md) — правила использования AI, ручной проверки
и верификации.

Backend-тесты включают unit/API tests и отдельный интеграционный сценарий
`tests/integration/`, который проходит через HTTP API, сервисный слой и
изолированную SQLite. Проверки фронтенда используют встроенный Node test runner
и не требуют npm-пакетов:

```powershell
pytest -q tests
node --test tests/frontend/*.test.js
```

## Security и эксплуатация

См. [модель угроз](security/threat-model.md),
[политику AI-инструментов и данных](security/tool-data-policy.md),
[security scan policy](security/scan-policy.md) и
[ограничения по Module 5](security/extension-notes.md).
GitHub Actions публикует отчёты Bandit и `pip-audit` и сохраняет диагностику
Compose-стека как артефакт workflow.

После запуска Compose-стека можно проверить сервисы и сохранить JSON-отчёт:

```powershell
python ops/diagnose.py --output ops/diagnostic-report.json
```

Инструкция настройки production-сервиса на Railway и GitHub Actions находится
в [`docs/railway-deploy.md`](docs/railway-deploy.md). Workflow выполняет deploy
только после успешной CI-проверки, при push в `main` и заданных Railway
variables/secrets.
