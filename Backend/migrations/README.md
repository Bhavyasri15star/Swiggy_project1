# Superseded by Alembic

These four `.sql` files are kept as a historical record of exactly what
was manually run against the database (each was applied by hand via a
one-off `psycopg2` script — there was no migration tooling at the time).

**All schema changes now go through `Backend/alembic/`, not new files
here.** Each of these four migrations has an equivalent, rollback-capable
revision under `alembic/versions/`, and the live database is stamped at
that history's head — so from here on:

```bash
cd Backend

# create a new migration (edit the generated file's upgrade()/downgrade())
alembic revision -m "describe the change"

# or, to diff core/models.py against the live schema automatically
alembic revision --autogenerate -m "describe the change"

# apply pending migrations
alembic upgrade head

# undo the most recent migration
alembic downgrade -1
```

Do not run these `.sql` files again — they're already applied, and
running them a second time will error (e.g. "column already exists").
