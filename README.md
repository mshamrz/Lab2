# Spry

Meeting list, monorepo skeleton for the course lab. See `PROJECT.md` for the
repository structure and contract, `docs/decision-monorepo.md` for why this
is one repository.

## Run locally

Requires Docker Desktop.

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (docs at `/docs`)
- Postgres: localhost:5432 (user/pass/db: `spry`/`spry`/`spry`)

The backend runs `alembic upgrade head` before starting, so the `meetings`
table exists on first boot.

## Lint

```bash
cd backend && pip install ruff && ruff check .
cd frontend && npm install && npm run lint
```

## Deploy

See `Makefile` and `.github/workflows/deploy.yml`. Deploy targets assume AWS
CLI is configured (`aws configure`) and the infrastructure described in
`docs/aws-setup.md` already exists.
