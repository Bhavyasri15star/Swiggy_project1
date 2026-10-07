# Swiggy Clone

A restaurant discovery demo: React frontend, a FastAPI backend for
restaurant/menu/order data, and a separate Express + Prisma service for
authentication (password + email OTP via Mailjet) — one shared PostgreSQL
database, Redis as an optional cache.

Full component breakdown and diagram: **[ARCHITECTURE.md](ARCHITECTURE.md)**.
Deploying to a public URL: **[DEPLOY.md](DEPLOY.md)**.

## Prerequisites

- Python 3.13, Node 20+, PostgreSQL, Redis
- A Postgres database named `swiggy_clone` (user `swiggy_user` / password
  `12345`, or override via `DATABASE_URL` — see below)

## Setup

```bash
# Backend
cd Backend
pip install -r requirements.txt

# AuthService
cd ../AuthService
npm install
cp .env.example .env   # fill in JWT_SECRET (must match Backend's — see below)
                        # and, for real OTP email, MAILJET_API_KEY/API_SECRET/SENDER_EMAIL
npx prisma db push     # creates the auth.users / auth.email_otps tables

# Frontend
cd ../Frontend/Swiggy_Clone
npm install
cp .env.example .env.local   # defaults already point at localhost, fine for local dev
```

Backend has no `.env` file of its own — it reads `DATABASE_URL`,
`JWT_SECRET`, `REDIS_HOST`/`REDIS_PORT`, and `CORS_ORIGINS` directly from
the environment, each with a working local default baked in (see
`Backend/core/database.py`, `core/auth.py`, `core/redis_client.py`). Set
`JWT_SECRET` as a real environment variable if you want it to definitely
match AuthService's — otherwise both fall back to the same demo value, so
local dev works either way.

## Run (one terminal per service)

```bash
# Backend — http://127.0.0.1:8000
cd Backend && uvicorn main:app --reload

# AuthService — http://localhost:4000
cd AuthService && npm run dev

# Frontend — http://localhost:3000
cd Frontend/Swiggy_Clone && npm start
```

Or, once Docker is available: `docker compose up --build` starts all five
pieces (the three services + Postgres + Redis) in one command — see
`docker-compose.yml`. This hasn't been verified with an actual `docker
build` on this machine (Docker isn't installed here); the parts that
matter most (schema creation + demo-data seeding on a fresh database) were
verified directly against a real Postgres instance instead — see
`Backend/docker-entrypoint.py`'s docstring.

First run against an empty database: `cd Backend && python
docker-entrypoint.py` creates the schema and seeds demo restaurant/menu
data (idempotent — safe to run again, it skips seeding if data already
exists). For AuthService, `npx prisma db push` (in the setup step above)
is what actually creates `auth.users`/`auth.email_otps` — it isn't
automatic on `npm run dev`/`npm start`; only the Docker image runs it for
you on container start.

## Test

```bash
cd Backend
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

Covers the highest-value logic: `cancel_order`'s business rules (10-minute
window, status gating, ownership), UUID validation happening before any DB
session opens, and the day-gating comparison. Repository/DB tests run
against a dedicated `test_swiggy_clone` Postgres schema — created fresh and
dropped each run, so they never touch real data (see `Backend/tests/conftest.py`).
Runs automatically in CI (`.github/workflows/ci.yml`) against a throwaway
Postgres container.

AuthService and the frontend have no automated tests yet — the manual
path (sign up/log in, browse, order, view history) is still how those get
exercised.

## Demo path

1. Start all three services (above).
2. Open `http://localhost:3000`.
3. Sign up (top-right) — either email/password, or email OTP (needs
   Mailjet configured in `AuthService/.env`, otherwise the code is logged
   to the AuthService console instead of emailed).
4. Browse restaurants → pick one → add items to cart → checkout.
5. Place the order, then check "Orders" to see it in your order history.

## Known limitations

- AuthService and the frontend have no automated tests yet (Backend does — see above).
- Local dev's Redis runs inside WSL and stops when WSL idles out — wake it
  with `wsl service redis-server status` (no sudo needed; the service is
  enabled to auto-start once WSL itself is up). Not needed for
  correctness — every Redis-dependent path (caching, rate limiting)
  degrades gracefully on a Redis error instead of failing the request —
  only for cache-hit performance and rate-limit enforcement while it's down.
