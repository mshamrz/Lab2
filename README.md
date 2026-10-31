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

## Infrastructure

The infrastructure is written as Terraform in `infra/` and applied by
HCP Terraform (organization `ooad-mshamrz`, workspace `spry-dev`).

| File | What it describes |
|---|---|
| `versions.tf` | Terraform and provider versions, the HCP Terraform workspace, default tags |
| `variables.tf`, `terraform.tfvars` | Inputs. Non-secret values are in `terraform.tfvars` |
| `auth.tf` | Cognito user pool, Google provider, client, domain, branding |
| `ai.tf` | The agenda parser: role, Lambda function, function URL, code bucket |
| `outputs.tf` | Ids and the parser URL |

**How a change reaches AWS.** Open a pull request that changes `infra/`. HCP
Terraform posts a plan as a check. Read it, merge, then confirm the run in
HCP Terraform (**Confirm & Apply**). Nobody applies from a laptop.

**Secrets** (`google_client_id`, `google_client_secret`) are Terraform variables
in the workspace. They are never committed.

**Useful commands**

    make infra-fmt        # terraform fmt -check
    make infra-validate   # init without the backend, then validate
    make infra-plan       # a speculative plan in HCP Terraform (terraform login first)

`infra/reports.yml` is the Lab 5 CloudFormation template. It is not migrated,
see `docs/adr/0007-terraform.md`.