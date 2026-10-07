# Express + Prisma auth service. Build context must be the AuthService/ directory.
FROM node:20-slim

WORKDIR /app

# Install deps first so this layer is cached across code-only changes.
# (Includes devDependencies — the prisma CLI, needed below — this project
# has no separate prod/dev split worth a multi-stage build for.)
COPY package*.json ./
RUN npm ci

COPY . .

# Generates the Prisma client from schema.prisma into node_modules.
RUN npx prisma generate

EXPOSE 4000

# `prisma db push` syncs the "auth" schema (creates the users table on a
# fresh database; no-ops if it already matches schema.prisma) — this
# project uses db push rather than versioned Prisma migrations (no
# prisma/migrations/ directory exists).
#
# Confirmed in production: db push's `?schema=auth` targeting silently
# ALTERs this shared role's default search_path to "auth" as a side effect
# -- even on a no-op push -- which then breaks every other service sharing
# this role (the FastAPI backend's unqualified "orders"/"coupons" etc.
# queries start failing with "relation does not exist"). The backend's own
# per-connection `SET search_path` isn't a complete fix for this since
# Neon's pooled endpoint can hand out a fresh backend session that never
# saw that SET. So: reset the role's default back to "public" immediately
# after every db push, before the server starts -- self-healing on every
# restart instead of needing a manual fix each time this container reboots.
CMD ["sh", "-c", "npx prisma db push --skip-generate && echo 'ALTER ROLE CURRENT_USER SET search_path = public;' | npx prisma db execute --stdin --schema=prisma/schema.prisma && node src/index.js"]
