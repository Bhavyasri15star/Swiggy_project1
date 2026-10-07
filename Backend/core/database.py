import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://swiggy_user:12345@localhost:5432/swiggy_clone",
)

engine = create_engine(DATABASE_URL)


# Neon's pooled endpoint doesn't support the `options=-c search_path=...`
# startup parameter this project used to rely on, and in production this
# role (neondb_owner) is shared with AuthService's Prisma client, which
# targets a different schema ("auth") via a `?schema=` connection-string
# param. Prisma's schema targeting can persist an ALTER ROLE ... SET
# search_path at the database level as a side effect (confirmed: this
# actually happened and broke every other connection using this role,
# including this app's, until search_path was reset) -- so every
# connection this app opens explicitly sets its own search_path instead
# of trusting whatever the role's current default happens to be.
@event.listens_for(engine, "connect")
def _set_search_path(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('SET search_path TO "$user", public')
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

