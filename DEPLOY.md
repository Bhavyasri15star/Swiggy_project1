# Deploying to Render (public URL)

Stack: **GitHub** (Render needs GitHub/GitLab/Bitbucket — it doesn't support
this repo's actual remote, Azure DevOps) + **Neon** (external free Postgres —
Render's own free Postgres expires after 30 days; Neon's doesn't) +
**Render** (web services for backend/authservice/frontend, plus Render's own
free Redis, which has no expiration).

Prereqs already done: Dockerfiles for all three services, `render.yaml`
(Render Blueprint — validated, deploys backend/authservice/frontend/redis
in one shot), and `Backend/docker-entrypoint.py`, which creates the schema
and seeds demo data automatically the first time it runs against an empty
database — so Neon's fresh, empty database gets populated on first deploy
with no manual step.

## 1. Push this repo to GitHub (needs your account — I can't create one)

1. Create a new empty repository on GitHub (no README/gitignore — keep it empty).
2. Give me the repo URL and I'll add it as a second remote and push (your
   existing Azure DevOps remote is untouched).

## 2. Create a Neon project (needs your account)

1. Sign up at neon.tech (free, no card required for the free tier).
2. Create a project → copy its connection string. It looks like:
   `postgresql://<user>:<password>@<host>/<dbname>?sslmode=require`
3. You'll use this same string twice in step 4: once as-is for `backend`,
   once with `&schema=auth` appended for `authservice` (Prisma isolates its
   `users` table into that schema, same as the local dev setup).

## 3. Deploy the Render Blueprint (needs your account)

1. Sign up at render.com (free, no card required for the free tier used here).
2. New → Blueprint → connect the GitHub repo from step 1.
3. Render reads `render.yaml` and creates: `backend`, `authservice`,
   `frontend` (all Docker-based web services) and `swiggy-redis` (free
   Key Value store) — all in one step.

## 4. Set the env vars `render.yaml` left blank

In the Render dashboard, per service:

**backend:**
- `DATABASE_URL` → the Neon connection string from step 2
- `JWT_SECRET` → generate with `python -c "import secrets; print(secrets.token_hex(32))"` — **must match authservice's**
- `CORS_ORIGINS` → the frontend service's `onrender.com` URL (visible once it's created)

**authservice:**
- `DATABASE_URL` → same Neon connection string **+ `&schema=auth`**
- `JWT_SECRET` → same value as backend's
- `CORS_ORIGINS` → same as backend's

(`REDIS_HOST`/`REDIS_PORT` for backend are already wired via `fromService` in
`render.yaml` — nothing to set manually there.)

## 5. Rebuild the frontend with the real backend/authservice URLs

CRA bakes `REACT_APP_API_URL`/`REACT_APP_AUTH_URL` in at build time, so they
can't be plain runtime env vars — once `backend` and `authservice` have their
`onrender.com` URLs, edit `render.yaml`'s `frontend.dockerBuildArgs` (or set
them directly in the dashboard's build args UI) and trigger a redeploy of
just `frontend`.

## 6. Verify

```bash
curl https://<backend>.onrender.com/restaurants
curl https://<authservice>.onrender.com/
```

Then open the frontend's URL in a browser. First request to each free
service after 15 min idle takes ~30-60s (cold start) — expected, not broken.

## Known gaps / things to watch

- **Neon sleeps after 5 min idle**, auto-resumes on the next query — the
  first request after a quiet spell will be slower, not broken.
- **Render's free web services spin down after 15 min idle** — same effect,
  compounds with Neon's on a cold demo.
- The repo's git remote is Azure DevOps, not GitHub — step 1 adds GitHub as
  a *second* remote; nothing about Azure DevOps changes.
- The repo has an **unfinished interactive rebase** sitting in `.git` (`git
  status` still shows "editing a commit"), unrelated to this deploy —
  flagging again since it's been there a while; not something I've touched
  per your earlier call to handle it yourself.
- Docker itself isn't installed on this machine, so these Dockerfiles are
  unbuilt/untested by an actual local `docker build` — Render builds them
  remotely, which will be the first real build. The custom risky part
  (`docker-entrypoint.py`'s schema-creation + seeding) was verified directly
  against a real Postgres database, not just written and hoped for.
