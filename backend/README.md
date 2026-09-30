# FRZR BURN — Backend

FastAPI service for the Islander Cyber Society CTF-gated smart mini fridge. Students earn unlock eligibility by solving CTF challenges; the backend validates their TOTP-based codes and manages credits.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker + Docker Compose | latest | [docker.com](https://www.docker.com/get-started/) |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd backend
uv sync
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in every value. See the [Environment Variables](#environment-variables) table below. The two most important ones to get right are `TOTP_ENCRYPTION_KEY` and `DATABASE_URL`.

Generate a fresh `TOTP_ENCRYPTION_KEY`:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Start a database

**Option A — Local Docker (recommended for development)**

```bash
docker compose up -d db
```

This starts a Postgres 16 container on port `5432`. Your `.env` `DATABASE_URL` should match:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fridge_dev
```

**Option B — Supabase (staging / production)**

Create a project at [supabase.com](https://supabase.com) (free tier is sufficient). Copy the direct connection string from **Project Settings → Database → Connection string (URI)**. Use the pooler connection string (port `6543`) if deploying to a serverless environment.

> Use **separate Supabase projects** for dev and prod — never share one instance between a local migration run and a live deployment.

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Start the API server

```bash
uv run uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`.
Auto-generated interactive docs: `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string, e.g. `postgresql+asyncpg://postgres:postgres@localhost:5432/fridge_dev` |
| `TOTP_ENCRYPTION_KEY` | Yes | Fernet key used to encrypt TOTP secrets at rest. Generate with `Fernet.generate_key()`. **If this leaks, TOTP secrets are exposed.** |
| `CLERK_SECRET_KEY` | Yes | Backend-only Clerk key for verifying admin session JWTs. Get from the Clerk dashboard. |
| `CLERK_PUBLISHABLE_KEY` | Yes | Clerk publishable key — used to derive the JWKS URL for JWT verification. |
| `RANGE_WEBHOOK_SECRET` | Yes | HMAC-SHA256 secret shared with the CTF range. Used to verify `flag-captured` webhook payloads. |
| `RATE_LIMIT_PER_MINUTE` | No | Max code-validation requests per device per minute. Default: `10` |
| `CORS_ORIGINS` | No | JSON array of allowed frontend origins. Default: `["http://localhost:3000"]` |
| `CREDIT_CONVERSION_RATE` | No | Points divided by this value equals credits awarded. Default: `10` |

**Never commit a real `.env` file.** The `.env.example` is safe to commit; `.env` is gitignored.

---

## Running Tests

```bash
uv run pytest
```

Tests use an in-memory SQLite database and do not require a running Postgres or valid Clerk/Supabase credentials.

---

## Running with Docker Compose (full stack)

To run both the database and API together:

```bash
docker compose up
```

The API will be at `http://localhost:8000`. Run migrations against the compose DB before starting the API:

```bash
docker compose up -d db
uv run alembic upgrade head
docker compose up api
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, router registration
│   ├── core/
│   │   ├── config.py        # All settings (loaded from .env)
│   │   ├── security.py      # TOTP, Fernet encryption, Clerk JWT, HMAC verification
│   │   ├── dependencies.py  # FastAPI Depends — admin auth, device auth, DB session
│   │   └── rate_limit.py    # SlowAPI rate limiter instance
│   ├── db/
│   │   ├── session.py       # Async SQLAlchemy engine and session factory
│   │   └── models.py        # All 8 ORM models
│   ├── schemas/             # Pydantic v2 request/response schemas
│   └── routers/
│       ├── students.py      # Enroll, list, update, reset TOTP
│       ├── devices.py       # Code validation (rate-limited), heartbeat, state
│       ├── events.py        # flag-captured webhook (HMAC verified)
│       ├── dashboard.py     # Unlock event log, credit ledger, device list
│       ├── items.py         # Item catalog
│       └── redemptions.py   # Credit redemptions
├── migrations/
│   ├── env.py               # Async Alembic env
│   └── versions/
│       └── 0001_initial_schema.py
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## API Overview

All admin endpoints require an `Authorization: Bearer <clerk_jwt>` header.
Device endpoints require an `X-Device-Key: <api_key>` header.
The webhook endpoint requires an `X-Range-Signature: sha256=<hmac>` header.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/students` | Admin | Enroll a student; returns provisioning URI once |
| `GET` | `/students` | Admin | List students (paginated) |
| `GET` | `/students/{id}` | Admin | Student detail |
| `PATCH` | `/students/{id}` | Admin | Update name/email/active |
| `POST` | `/students/{id}/reset-totp` | Admin | Invalidate TOTP and issue new secret |
| `POST` | `/devices/{id}/validate-code` | Device | Validate 10-digit code — always returns 200 |
| `POST` | `/devices/{id}/events` | Device | Heartbeat or forced-open log |
| `GET` | `/devices/{id}/state` | Device | Pending commands (always null in v1) |
| `POST` | `/events/flag-captured` | HMAC/Bearer | CTF range webhook — grants unlock eligibility |
| `GET` | `/dashboard/unlock-events` | Admin | Filterable event log |
| `GET` | `/students/{id}/ledger` | Admin | Credit history and balance |
| `GET` | `/devices` | Admin | All devices with online status |
| `GET` | `/items` | Admin | Item catalog |
| `POST` | `/items` | Admin | Add item |
| `POST` | `/redemptions` | Admin | Redeem credits for an item |

Error responses always follow: `{"error": {"code": "...", "message": "...", "details": {}}}`.
Business declines (invalid code, no eligibility) return `200` with `{"valid": false, "reason": "..."}` — not `4xx`.

---

## Architecture Notes

- The backend is the **only component with database access**. The ESP32 and frontend never connect to Postgres directly.
- TOTP secrets are encrypted with Fernet before storage and never returned in any API response after initial enrollment.
- `POST /devices/{id}/validate-code` is security-critical — rate limiting and constant-time TOTP comparison are enforced, not deferred.
- Full architecture decisions are documented in [`claude_docs/DECISIONS.md`](claude_docs/DECISIONS.md). Read it before changing the code-validation flow or data model.
