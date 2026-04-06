# Model Registry HW

## 1) Проблемы текущего состояния

- Нет единого реестра: модели лежат только в папках.
- Нельзя понять, какая версия актуальна и где `production`.
- Нет метаданных: параметры, метрики, датасет, команда, run_id.
- Нет истории изменений и прозрачных переходов между стадиями.
- Нельзя быстро найти модель по имени/команде/стадии.
- Нет стандартного API для интеграции с пайплайнами.

## 2) Требования

### Функциональные

- Регистрация модели по уникальному имени.
- Создание версий модели с метаданными (`parameters`, `metrics`, `tags`, `run_id`).
- Хранение артефактов версии в объектном хранилище.
- Просмотр, обновление, удаление моделей и версий.
- Перевод версии между стадиями `none/staging/production/archived`.
- Гарантия одной `production` версии на модель.
- Поиск/фильтрация моделей и версий.

### Нефункциональные

- Простое локальное развертывание через Docker Compose.
- Надежное хранение метаданных (PostgreSQL, транзакции).
- Изоляция артефактов и S3-совместимость (MinIO).
- Расширяемая структура кода без оверинжиниринга.
- Тестируемость API и бизнес-логики.

## 3) Архитектура и технологии

Клиент ходит только в HTTP-слой; метаданные и бинарные артефакты разделены: БД не хранит веса, объектное хранилище не хранит связи и стадии.

```mermaid
graph TD
    mlTeam[MLTeam] -->|REST| fastapi[FastAPI]
    fastapi --> repo[RepositoryLayer]
    repo --> postgres[(PostgreSQL)]
    fastapi --> storage[StorageService]
    storage --> minio[(MinIO)]
```

**FastAPI** — REST и OpenAPI из коробки, валидация через Pydantic совпадает с типами в коде. Проще, чем собирать то же на «голом» Flask без схем.

**PostgreSQL** — ACID, ограничения уникальности и FK (модель → версии), JSONB для гибких `parameters`/`metrics`/`tags` без отдельной схемы на каждый ключ. SQLite проще, но хуже для нескольких воркеров и жёстких constraint’ов под прод.

**MinIO** — S3-совместимый API: те же клиенты и паттерны, что в облаке; можно поднять локально в Docker без внешних сервисов. Хранить гигабайты весов в таблицах БД нецелесообразно.

**Repository-слой** — запросы к БД не размазаны по хендлерах: проще тестировать и менять SQL без правок HTTP.

**Alembic** — миграции как код, воспроизводимое обновление схемы между окружениями; ручные SQL-скрипты без версий легко рассинхронизировать с ORM.

## 4) API и схема БД

### API

- `POST /api/v1/models`
- `GET /api/v1/models`
- `GET /api/v1/models/{name}`
- `PATCH /api/v1/models/{name}`
- `DELETE /api/v1/models/{name}`
- `POST /api/v1/models/{name}/versions`
- `GET /api/v1/models/{name}/versions`
- `GET /api/v1/models/{name}/versions/{version}`
- `PATCH /api/v1/models/{name}/versions/{version}`
- `PUT /api/v1/models/{name}/versions/{version}/stage`
- `POST /api/v1/models/{name}/versions/{version}/artifacts`
- `GET /api/v1/models/{name}/versions/{version}/artifacts/{filename}`

### DB schema

`registered_models`
- `id` PK
- `name` UNIQUE NOT NULL
- `description`
- `team`
- `created_at`, `updated_at`

`model_versions`
- `id` PK
- `model_id` FK -> `registered_models.id`
- `version` (уникально в паре `model_id + version`)
- `stage`
- `parameters` JSON(B)
- `metrics` JSON(B)
- `tags` JSON(B)
- `artifact_uri`
- `run_id`
- `description`
- `created_at`, `updated_at`
