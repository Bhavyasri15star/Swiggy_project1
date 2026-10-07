import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Must match JWT_SECRET in AuthService/.env — that service issues the tokens,
# this only verifies them. The fallback below matches AuthService/.env.example's
# demo value so the two work together out of the box; override both with a
# real secret outside of local development.
JWT_SECRET = os.environ.get(
    "JWT_SECRET",
    "3680007c9f90e7b853a37f93ae37feb010e234eebf079e2750c0130f94dcc79c",
)
JWT_ALGORITHM = "HS256"

# auto_error=False so a missing/malformed header raises our own message
# below (matching every existing caller's expectation) instead of FastAPI's
# generic "Not authenticated" -- same wire format and error behavior as the
# plain Header() this replaced, just exposed to Swagger UI as a proper
# security scheme (one global "Authorize" button) instead of a raw
# per-request header field, which had a reproducible paste-registration
# bug in Swagger UI's own frontend.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: requires a valid 'Authorization: Bearer <token>'
    header carrying a JWT issued by AuthService. Returns its decoded claims
    (sub, email, name). Raises 401 on anything else."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload
