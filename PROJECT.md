# PROJECT.md — Spry (monorepo)

Structure only. No implementation code lives in this file.

## Layout

```
spry/
├── backend/            FastAPI service: HTTP API, ORM models, migrations
│   ├── app/
│   │   ├── main.py         FastAPI app instance, CORS, router registration
│   │   ├── database.py     SQLAlchemy engine + session factory
│   │   ├── models.py       SQLAlchemy ORM models (Meeting)
│   │   ├── schemas.py      Pydantic request/response models
│   │   └── routers/
│   │       └── meetings.py GET /api/meetings, POST /api/meetings
│   ├── alembic/             migration scripts, one file per schema change
│   ├── alembic.ini
│   ├── requirements.txt    pinned dependency versions
│   ├── pyproject.toml      ruff config
│   └── Dockerfile          python:3.12-slim, installs requirements, runs uvicorn
│
├── frontend/           React SPA: one page, one list, one form
│   ├── src/
│   │   ├── main.tsx         React entry point
│   │   ├── App.tsx          page layout
│   │   ├── api.ts           fetch wrapper for the backend contract below
│   │   └── components/
│   │       ├── MeetingList.tsx   renders the list of meetings
│   │       └── MeetingForm.tsx   form that POSTs a new meeting
│   ├── index.html
│   ├── package.json        pinned dependency versions
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── eslint.config.js
│   └── Dockerfile          node:20-slim build stage, nginx:1.27-alpine serve stage
│
├── docker-compose.yml   postgres, backend, frontend — the only command a new
│                        developer runs is `docker compose up`
├── Makefile             deploy-frontend, deploy-backend (used by CI and by hand)
├── .github/workflows/   ci.yml (lint+test on every push), deploy.yml (on main)
└── docs/                decisions written down during the course
```

## Contract: `GET /api/meetings` and `POST /api/meetings`

A **Meeting**:

| field           | type                          | notes                        |
|-----------------|-------------------------------|-------------------------------|
| `id`            | integer                       | server-generated, primary key |
| `title`         | string, 1–200 chars            | required                      |
| `starts_at`     | string, ISO 8601 UTC (`...Z`)  | required                      |
| `ends_at`       | string, ISO 8601 UTC (`...Z`)  | required, must be > `starts_at` |
| `attendee_count`| integer ≥ 0                    | required                      |

`GET /api/meetings` → `200`, JSON array of Meeting, ordered by `starts_at` ascending.

`POST /api/meetings` → body: `title`, `starts_at`, `ends_at`, `attendee_count`
(no `id`). Returns `201` with the created Meeting including its `id`.
Returns `422` with a validation error if a field is missing, empty, or if
`ends_at <= starts_at`.

## docker-compose services

| service   | image / build       | port (host:container) | depends on                 | readiness                         |
|-----------|----------------------|------------------------|------------------------------|-------------------------------------|
| postgres  | `postgres:16`         | 5432:5432               | —                             | healthcheck: `pg_isready`           |
| backend   | build: `./backend`    | 8000:8000               | postgres, `condition: service_healthy` | starts only after Postgres passes its healthcheck; runs `alembic upgrade head` on container start, before `uvicorn` |
| frontend  | build: `./frontend`   | 5173:5173               | backend (not a hard block — the SPA can load before the API is ready; requests just fail until it is) | none required |

## Explicitly not included

No Redis, no Celery, no nginx reverse proxy in front of compose, no second
database, no Kubernetes manifest. Add nothing beyond what is listed above.
