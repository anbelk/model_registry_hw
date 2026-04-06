# Model Registry

Минимальный model registry на FastAPI + PostgreSQL + MinIO.

## Запуск

```bash
docker compose up --build
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Тесты

```bash
pytest -q
```

## Миграции

```bash
alembic upgrade head
```
